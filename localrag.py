import logging
# Configurer le logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger.info("START")
logger.debug("Import Modules")
import time
import torch
import ollama
from prettytable import PrettyTable
import os
from openai import OpenAI
import argparse
import json
logger.debug("Import Modules : Done.")

logger.debug("Setting Vars")
my_filename       = "vault.txt"                    ### FILENAME
OLLAMA_HOST       = '192.168.0.1'                  ### OLLAMA HOST
text_to_remove    = " - Dernière modification le 19 mai 2024 - Document généré le 03 juin 2024"
oclient           = ollama.Client(host=OLLAMA_HOST)
EMBED_MODEL       = None
embed_models_list = []
models_list       = oclient.list()
# ANSI escape codes for console colors
PINK              = '\033[95m'
CYAN              = '\033[96m'
YELLOW            = '\033[93m'
NEON_GREEN        = '\033[92m'
RESET_COLOR       = '\033[0m'

logger.debug("Finding available models")
for model in models_list['models']:
    current_model_name = model['name']
    if "embed" not in current_model_name:
        continue
    else:
        embed_models_list.append(current_model_name)

logger.debug("Creating PrettyTable")
table = PrettyTable()
table.field_names = ["ID", "Name"]
# Ajouter les données au tableau
i = 1
for item in embed_models_list:
    table.add_row([i, item])
    i += 1

logger.debug("Display PrettyTable")
print(table)

while EMBED_MODEL is None:
    try:
        choix = int(input("Veuillez choisir un modèle pour l'embedding en entrant l'ID correspondant : "))
        # Vérifier si le choix est valide et paramétrer le workspace
        choix = choix - 1
        EMBED_MODEL = embed_models_list[choix]
        print(f"Vous avez choisi le model pour embed : {EMBED_MODEL}")
    except ValueError:
        print("Entrée invalide. Veuillez entrer un nombre correspondant à l'ID.")

logging.info(f"OLLAMA HOST : {OLLAMA_HOST}")
logging.info(f"EMBED MODEL : {EMBED_MODEL}")
input("Press Enter to continue... or CTRL+C to abort")

logger.debug("Setting Vars : Done.")

# Function to open a file and return its contents as a string
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Function to get relevant context from the vault based on user input
def get_relevant_context(rewritten_input, vault_embeddings, vault_content, top_k=3):
    if vault_embeddings.nelement() == 0:  # Check if the tensor has any elements
        return []
    # Encode the rewritten input
    input_embedding = oclient.embeddings(model='mxbai-embed-large', prompt=rewritten_input)["embedding"]
    # Compute cosine similarity between the input and vault embeddings
    cos_scores = torch.cosine_similarity(torch.tensor(input_embedding).unsqueeze(0), vault_embeddings)
    # Adjust top_k if it's greater than the number of available scores
    top_k = min(top_k, len(cos_scores))
    # Sort the scores and get the top-k indices
    top_indices = torch.topk(cos_scores, k=top_k)[1].tolist()
    # Get the corresponding context from the vault
    relevant_context = [vault_content[idx].strip() for idx in top_indices]
    return relevant_context

def rewrite_query(user_input_json, conversation_history, ollama_model):
    user_input = json.loads(user_input_json)["Query"]
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-2:]])
    prompt = f"""Rewrite the following query by incorporating relevant context from the conversation history.
    The rewritten query should:
    
    - Preserve the core intent and meaning of the original query
    - Expand and clarify the query to make it more specific and informative for retrieving relevant context
    - Avoid introducing new topics or queries that deviate from the original query
    - DONT EVER ANSWER the Original query, but instead focus on rephrasing and expanding it into a new query
    
    Return ONLY the rewritten query text, without any additional formatting or explanations.
    
    Conversation History:
    {context}
    
    Original query: [{user_input}]
    
    Rewritten query: 
    """
    response = client.chat.completions.create(
        model       = ollama_model,
        messages    = [{"role": "system", "content": prompt}],
        max_tokens  = 200,
        n           = 1,
        temperature = 0.1,
    )
    rewritten_query = response.choices[0].message.content.strip()
    return json.dumps({"Rewritten Query": rewritten_query})
   
def ollama_chat(user_input, system_message, vault_embeddings, vault_content, ollama_model, conversation_history):
    conversation_history.append({"role": "user", "content": user_input})
    
    if len(conversation_history) > 1:
        query_json = {
            "Query": user_input,
            "Rewritten Query": ""
        }
        rewritten_query_json = rewrite_query(json.dumps(query_json), conversation_history, ollama_model)
        rewritten_query_data = json.loads(rewritten_query_json)
        rewritten_query = rewritten_query_data["Rewritten Query"]
        print(PINK + "Original Query: " + user_input + RESET_COLOR)
        print(PINK + "Rewritten Query: " + rewritten_query + RESET_COLOR)
    else:
        rewritten_query = user_input
    
    relevant_context = get_relevant_context(rewritten_query, vault_embeddings, vault_content)
    if relevant_context:
        context_str = "\n".join(relevant_context)
        print("Context Pulled from Documents: \n\n" + CYAN + context_str + RESET_COLOR)
    else:
        print(CYAN + "No relevant context found." + RESET_COLOR)
    
    user_input_with_context = user_input
    if relevant_context:
        user_input_with_context = user_input + "\n\nRelevant Context:\n" + context_str
    
    conversation_history[-1]["content"] = user_input_with_context
    
    messages = [
        {"role": "system", "content": system_message},
        *conversation_history
    ]
    
    response = client.chat.completions.create(
        model=ollama_model,
        messages=messages,
        max_tokens=2000,
    )
    
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})
    
    return response.choices[0].message.content

# Parse command-line arguments
print(NEON_GREEN + "Parsing command-line arguments..." + RESET_COLOR)
parser = argparse.ArgumentParser(description="Ollama Chat")
parser.add_argument("--model", default="llama3", help="Ollama model to use (default: llama3)")
args = parser.parse_args()

# Configuration for the Ollama API client
print(NEON_GREEN + "Initializing Ollama API client..." + RESET_COLOR)
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='llama3'
)

# Load the vault content
print(NEON_GREEN + "Loading vault content..." + RESET_COLOR)
vault_content = []
if os.path.exists("vault.txt"):
    with open("vault.txt", "r", encoding='utf-8') as vault_file:
        vault_content = vault_file.readlines()

# Generate embeddings for the vault content using Ollama
print(NEON_GREEN + "Generating embeddings for the vault content..." + RESET_COLOR)
vault_embeddings = []

tic = time.perf_counter()
for content in vault_content:
    print(YELLOW + 'QUERY' + RESET_COLOR)
    print(content)
    if text_to_remove:
        content = content.replace(text_to_remove, ' ')
    response = oclient.embeddings(model=EMBED_MODEL, prompt=content)
    
    print(NEON_GREEN + 'Done' + RESET_COLOR)
    print(YELLOW + 'APPEND' + RESET_COLOR)
    vault_embeddings.append(response["embedding"])
    print(NEON_GREEN + 'Done' + RESET_COLOR)

logger.debug("Generate Embeddings : Done.")
toc = time.perf_counter()

if f"{toc - tic:0.4f}" > 1000:
    duration = toc - tic / 60
    print(f"Duration : {duration:0.4f} minutes")
else:
    print(f"Duration : {toc - tic:0.4f} seconds")

# Convert to tensor and print embeddings
logger.info("Converting embeddings to tensor...")
vault_embeddings_tensor = torch.tensor(vault_embeddings) 
logger.info("Embeddings for each line in the vault:")
print(vault_embeddings_tensor)

# Conversation loop
logger.info("Starting conversation loop...")
conversation_history = []
system_message = "You are a helpful assistant that is an expert at extracting the most useful information from a given text. Also bring in extra relevant infromation to the user query from outside the given context."

while True:
    logger.debug("User Loop")
    user_input = input(YELLOW + "Ask a query about your documents (or type 'quit' to exit): " + RESET_COLOR)
    if user_input.lower() == 'quit':
        break
    
    response = ollama_chat(user_input, system_message, vault_embeddings_tensor, vault_content, args.model, conversation_history)
    print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)

logger.info("End of File")
