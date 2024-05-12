import imaplib
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime, timedelta
import os
import re
import argparse
from bs4 import BeautifulSoup
import lxml
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def chunk_text(text, max_length=1000):
    # Normalize Unicode characters to the closest ASCII representation
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Remove sequences of '>' used in email threads
    text = re.sub(r'\s*(?:>\s*){2,}', ' ', text)

    # Remove sequences of dashes, underscores, or non-breaking spaces
    text = re.sub(r'-{3,}', ' ', text)
    text = re.sub(r'_{3,}', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)  # Collapse multiple spaces into one

    # Replace URLs with a single space, or remove them
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Normalize whitespace to single spaces, strip leading/trailing whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Split text into sentences while preserving punctuation
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 < max_length:
            current_chunk += (sentence + " ").strip()
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def save_chunks_to_vault(chunks):
    vault_path = "vault.txt"
    with open(vault_path, "a", encoding="utf-8") as vault_file:
        for chunk in chunks:
            vault_file.write(chunk.strip() + "\n")

def get_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text()

def save_plain_text_content(email_bytes, email_id):
    msg = BytesParser(policy=policy.default).parsebytes(email_bytes)
    text_content = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                text_content += part.get_payload(decode=True).decode(part.get_content_charset('utf-8'))
            elif part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'))
                text_content += get_text_from_html(html_content)
    else:
        if msg.get_content_type() == 'text/plain':
            text_content = msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8'))
        elif msg.get_content_type() == 'text/html':
            text_content = get_text_from_html(msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8')))

    chunks = chunk_text(text_content)
    save_chunks_to_vault(chunks)
    return text_content

def search_and_process_emails(imap_client, email_source, search_keyword, start_date, end_date):
    search_criteria = 'ALL'
    if start_date and end_date:
        search_criteria = f'(SINCE "{start_date}" BEFORE "{end_date}")'
    if search_keyword:
        search_criteria += f' BODY "{search_keyword}"'  # Ensure the correct combination of conditions

    print(f"Using search criteria for {email_source}: {search_criteria}")
    typ, data = imap_client.search(None, search_criteria)
    if typ == 'OK':
        email_ids = data[0].split()
        print(f"Found {len(email_ids)} emails matching criteria in {email_source}.")

        for num in email_ids:
            typ, email_data = imap_client.fetch(num, '(RFC822)')
            if typ == 'OK':
                email_id = num.decode('utf-8')
                print(f"Downloading and processing email ID: {email_id} from {email_source}")
                save_plain_text_content(email_data[0][1], email_id)
            else:
                print(f"Failed to fetch email ID: {num.decode('utf-8')} from {email_source}")
    else:
        print(f"Failed to find emails with given criteria in {email_source}. No emails found.")


def main():
    parser = argparse.ArgumentParser(description="Search and process emails based on optional keyword and date range.")
    parser.add_argument("--keyword", help="The keyword to search for in the email bodies.", default="")
    parser.add_argument("--startdate", help="Start date in DD.MM.YYYY format.", required=False)
    parser.add_argument("--enddate", help="End date in DD.MM.YYYY format.", required=False)
    args = parser.parse_args()

    start_date = None
    end_date = None

    # Check if both start and end dates are provided and valid
    if args.startdate and args.enddate:
        try:
            start_date = datetime.strptime(args.startdate, "%d.%m.%Y").strftime("%d-%b-%Y")
            end_date = datetime.strptime(args.enddate, "%d.%m.%Y").strftime("%d-%b-%Y")
        except ValueError as e:
            print(f"Error: Date format is incorrect. Please use DD.MM.YYYY format. Details: {e}")
            return
    elif args.startdate or args.enddate:
        print("Both start date and end date must be provided together.")
        return

    # Retrieve email credentials from environment variables
    gmail_username = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    outlook_username = os.getenv('OUTLOOK_USERNAME')
    outlook_password = os.getenv('OUTLOOK_PASSWORD')

    # Connect to Gmail's IMAP server
    M = imaplib.IMAP4_SSL('imap.gmail.com')
    M.login(gmail_username, gmail_password)
    M.select('inbox')

    # Connect to Outlook IMAP server
    H = imaplib.IMAP4_SSL('imap-mail.outlook.com')
    H.login(outlook_username, outlook_password)
    H.select('inbox')

    # Search and process emails from Gmail and Outlook
    search_and_process_emails(M, "Gmail", args.keyword, start_date, end_date)
    search_and_process_emails(H, "Outlook", args.keyword, start_date, end_date)

    M.logout()
    H.logout()

if __name__ == "__main__":
    main()
