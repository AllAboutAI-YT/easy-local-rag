# SuperEasy 100% Local RAG with Ollama

### YouTube Tutorial
https://www.youtube.com/watch?v=Oe-7dGDyzPM

### YouTube Updated Features
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/vFGng_3hDRk/0.jpg)](https://www.youtube.com/watch?v=vFGng_3hDRk)

### Setup
1. git clone https://github.com/AllAboutAI-YT/easy-local-rag.git
2. cd dir
3. pip install -r requirements.txt
4. Install Ollama (https://ollama.com/download)
5. ollama pull llama3 (etc)
6. ollama pull mxbai-embed-large
7. run upload.py (pdf, .txt, JSON)
8. run localrag.py

### Latest Updates V1.2
- New embeddings model mxbai-embed-large from ollama (1.2)
- Rewrite query function to improve retrival on vauge questions (1.2)
- Pick your model from the CLI (1.1)
  - python localrag.py --model mistral (llama3 is default) 
- Talk in a true loop with conversation history (1.1)
   
### My YouTube Channel
https://www.youtube.com/c/AllAboutAI

### What is RAG?
RAG is a way to enhance the capabilities of LLMs by combining their powerful language understanding with targeted retrieval of relevant information from external sources often with using embeddings in vector databases, leading to more accurate, trustworthy, and versatile AI-powered applications

### What is Ollama?
Ollama is an open-source platform that simplifies the process of running powerful LLMs locally on your own machine, giving users more control and flexibility in their AI projects. https://www.ollama.com
