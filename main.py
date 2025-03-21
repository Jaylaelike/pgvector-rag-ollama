import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import os
import docx
from PyPDF2 import PdfReader
import re
import csv
import json
import tiktoken  # Import tiktoken

# --- File Extraction and Processing Functions ---

def extract_text_from_file(filepath):
    # (Same as before, no changes)
    try:
        if filepath.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        elif filepath.lower().endswith(".docx"):
            doc = docx.Document(filepath)
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return "\n".join(full_text)
        elif filepath.lower().endswith(".pdf"):
            try:
                with open(filepath, "rb") as f:
                    reader = PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except Exception as pdf_error:
                print(f"Error reading PDF {filepath}: {pdf_error}")
                return ""
        else:
            print(f"Unsupported file type: {filepath}")
            return None
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return ""
    except Exception as e:
        print(f"An error occurred while processing {filepath}: {e}")
        return ""

def split_into_token_chunks(text, max_tokens=256, model_name="cl100k_base"):
    """Splits text into chunks of approximately max_tokens using tiktoken."""
    encoding = tiktoken.get_encoding(model_name)
    tokens = encoding.encode(text)
    chunks = []
    current_chunk = []

    for token in tokens:
        current_chunk.append(token)
        if len(current_chunk) >= max_tokens:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = []

    if current_chunk:  # Add any remaining tokens
        chunks.append(encoding.decode(current_chunk))
    return chunks



def process_directory_into_chunks(directory_path, max_tokens=256, model_name="cl100k_base"):
    """Processes all files in a directory, splitting text into token chunks."""
    all_chunks = []
    for root, _, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            text = extract_text_from_file(filepath)
            if text:
                chunks = split_into_token_chunks(text, max_tokens, model_name)
                all_chunks.extend(chunks)
    return all_chunks



# --- UI Functions ---

def browse_directory():
     # (Same as before, no changes)
    directory = filedialog.askdirectory()
    if directory:
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)

def browse_file():
    # (Same as before, no changes)
    filepath = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx"), ("PDF Files", "*.pdf"), ("All Files", "*.*")]
    )
    if filepath:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filepath)

def save_as_csv(chunks):
    """Saves the chunks to a CSV file."""
    if not chunks:
        return

    filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if filepath:
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Chunk"])  # Header row
                for chunk in chunks:
                    writer.writerow([chunk])
            tk.messagebox.showinfo("Success", f"Data saved to {filepath}")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not save to CSV: {e}")

def save_as_json(chunks):
    """Saves the chunks to a JSON file."""
    if not chunks:
        return

    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if filepath:
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(chunks, jsonfile, indent=4, ensure_ascii=False)
            tk.messagebox.showinfo("Success", f"Data saved to {filepath}")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not save to JSON: {e}")



def process_input():
    """Processes the input and enables save buttons, handling token-based chunking."""
    output_text.delete("1.0", tk.END)
    global chunk_data
    chunk_data = []

    max_tokens = 256  # Use the desired maximum token count
    model_name = "cl100k_base"  #  Good default for many tasks.

    try:
        max_tokens = int(max_tokens_entry.get())  # Get from entry, convert to int
    except ValueError:
        output_text.insert(tk.END, "Invalid max tokens value. Using default (256).\n")
        max_tokens = 256

    if directory_entry.get():
        try:
            chunk_data = process_directory_into_chunks(directory_entry.get(), max_tokens, model_name)
        except Exception as e:
            output_text.insert(tk.END, f"Error processing directory: {e}\n")

    elif file_entry.get():
        try:
            text = extract_text_from_file(file_entry.get())
            if text:
                chunk_data = split_into_token_chunks(text, max_tokens, model_name)
            else:
                output_text.insert(tk.END, "Could not extract text.\n")
        except Exception as e:
            output_text.insert(tk.END, f"Error processing file: {e}\n")
    else:
        output_text.insert(tk.END, "Please select a file or directory.\n")
        return

    for i, chunk in enumerate(chunk_data):
        output_text.insert(tk.END, f"--- Chunk {i+1} ---\n")
        output_text.insert(tk.END, chunk + "\n\n")

    save_csv_button.config(state=tk.NORMAL)
    save_json_button.config(state=tk.NORMAL)


# --- Main UI Setup ---

root = tk.Tk()
root.title("Document Splitter")
root.geometry("800x700")  # Adjusted height

# Style
style = ttk.Style()
style.configure('TButton', font=('Arial', 10))

# --- Directory Selection ---
directory_frame = tk.Frame(root)
directory_frame.pack(pady=10)
directory_label = tk.Label(directory_frame, text="Select Directory:")
directory_label.pack(side=tk.LEFT)
directory_entry = tk.Entry(directory_frame, width=50)
directory_entry.pack(side=tk.LEFT, padx=5)
browse_dir_button = ttk.Button(directory_frame, text="Browse", command=browse_directory)
browse_dir_button.pack(side=tk.LEFT)

# --- File Selection ---
file_frame = tk.Frame(root)
file_frame.pack(pady=10)
file_label = tk.Label(file_frame, text="Select File:")
file_label.pack(side=tk.LEFT)
file_entry = tk.Entry(file_frame, width=50)
file_entry.pack(side=tk.LEFT, padx=5)
browse_file_button = ttk.Button(file_frame, text="Browse", command=browse_file)
browse_file_button.pack(side=tk.LEFT)

# --- Max Tokens Input ---
max_tokens_frame = tk.Frame(root)
max_tokens_frame.pack(pady=10)
max_tokens_label = tk.Label(max_tokens_frame, text="Max Tokens per Chunk (default: 256):")
max_tokens_label.pack(side=tk.LEFT)
max_tokens_entry = tk.Entry(max_tokens_frame, width=10)
max_tokens_entry.insert(0, "256")  # Set default value
max_tokens_entry.pack(side=tk.LEFT)

# --- Process Button ---
process_button = ttk.Button(root, text="Process", command=process_input)
process_button.pack(pady=10)

# --- Save Buttons (initially disabled) ---
save_frame = tk.Frame(root)
save_frame.pack(pady=10)
save_csv_button = ttk.Button(save_frame, text="Save as CSV", command=lambda: save_as_csv(chunk_data), state=tk.DISABLED)
save_csv_button.pack(side=tk.LEFT, padx=5)
save_json_button = ttk.Button(save_frame, text="Save as JSON", command=lambda: save_as_json(chunk_data), state=tk.DISABLED)
save_json_button.pack(side=tk.LEFT)

# --- Output Text Area ---
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_text.pack(padx=10, pady=10)

chunk_data = []  # Global variable to store processed chunks

root.mainloop()