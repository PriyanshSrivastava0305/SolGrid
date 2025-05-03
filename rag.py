'''import requests
import os
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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") 
MODEL_ID = "llama-3.1-8b-instant" 

def query_groq_llm(prompt):
    """Query Groq API for text generation."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "system", "content": "You are an AI assistant."},
                     {"role": "user", "content": prompt}]
    }
    
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("Error:", response.status_code, response.text)
        return f"Error: {response.json()}"


def generate_answer(query):
    """Retrieve relevant articles and generate a response using Groq API."""
    vectorstore = FAISS.load_local("faiss_index", HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
                                   allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # Get relevant context from FAISS
    context = "\n\n".join([doc.page_content[:2000] for doc in retriever.get_relevant_documents(query)])  # Limit each doc to 2000 chars

    # Create final LLM prompt
    prompt = f"Answer the question based on the context below:\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"
    
    return query_groq_llm(prompt)


# Terminal-based Q&A loop
def terminal_qna():
    """Run the Q&A process in the terminal."""
    print("Welcome to the Q&A system! Type 'exit' to quit.")
    while True:
        query = input("Enter your question: ")
        
        if query.lower() == 'exit':
            print("Goodbye!")
            break
        
        answer = generate_answer(query)
        print("\nAnswer:", answer)

# Start the terminal Q&A loop
if __name__ == "__main__":
    terminal_qna()'''

import requests
import re
import os
import csv
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
MODEL_ID = "llama-3.1-8b-instant"

def query_groq_llm(prompt):
    """Query Groq API for text generation."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "system", "content": "You are an AI assistant."},
                     {"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("Error:", response.status_code, response.text)
        return f"Error: {response.json()}"

def generate_answer(query):
    """Retrieve relevant articles and generate a response using Groq API."""
    vectorstore = FAISS.load_local("faiss_index", HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
                                   allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    context = "\n\n".join([doc.page_content[:2000] for doc in retriever.get_relevant_documents(query)])

    prompt = f"Answer the question based on the context below:\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"
    return query_groq_llm(prompt)


def save_table_to_csv(table_str, filename="output.csv"):
    """Parse and save markdown-style table to CSV, skipping separator lines."""
    lines = table_str.strip().splitlines()
    table_data = []

    for line in lines:
        # Skip lines that are only separators (e.g., |----|-----|)
        if re.fullmatch(r'\s*\|?[\s\-|]+\|?\s*', line):
            continue
        if '|' in line:
            row = [cell.strip() for cell in line.strip('|').split('|')]
            table_data.append(row)

    if table_data:
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table_data)
        print(f"[✓] Table saved as {filename}")
    else:
        print("[!] No valid table content found to save.")

def terminal_qna():
    """Run the Q&A process in the terminal."""
    print("Welcome to the Q&A system! Type 'exit' to quit.")
    while True:
        query = input("Enter your question: ")

        if query.lower() == 'exit':
            print("Goodbye!")
            break

        answer = generate_answer(query)
        print("\nAnswer:\n", answer)

        if "table:" in query.lower():
            save_table_to_csv(answer)

if __name__ == "__main__":
    terminal_qna()

'''
For table output (and CSV saving):
Table: Show a summary of GDP per country
(The keyword table: is the trigger)
'''