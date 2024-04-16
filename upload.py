import os
import tkinter as tk
from tkinter import filedialog, messagebox
import PyPDF2
import re
import json

def convert_pdf_to_text():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                text = ''
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    if page.extract_text():
                        text += page.extract_text() + " "

            with open("vault.txt", "a", encoding="utf-8") as vault_file:
                vault_file.write(text.strip() + "\n\n")

            print(f"PDF content appended to vault.txt.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showwarning("Warning", "No PDF file selected.")

def read_json_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)

            with open("vault.txt", "a", encoding="utf-8") as vault_file:
                vault_file.write(json.dumps(data, indent=4))
                vault_file.write("\n\n")

            print(f"JSON content appended to vault.txt.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showwarning("Warning", "No JSON file selected.")

def append_text_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as text_file:
                content = text_file.read()

            with open("vault.txt", "a", encoding="utf-8") as vault_file:
                vault_file.write(content.strip() + "\n\n")

            print(f"Text content appended to vault.txt.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showwarning("Warning", "No text file selected.")

# Create the main window
root = tk.Tk()
root.title("File Uploader")

# Create buttons for each file type
pdf_button = tk.Button(root, text="Upload PDF", command=convert_pdf_to_text)
pdf_button.pack(pady=10)

json_button = tk.Button(root, text="Upload JSON", command=read_json_file)
json_button.pack(pady=10)

text_button = tk.Button(root, text="Upload Text", command=append_text_file)
text_button.pack(pady=10)

# Run the main event loop
root.mainloop()