import requests

import os
os.system("pip install --upgrade faiss-cpu langchain-community")

from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

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
