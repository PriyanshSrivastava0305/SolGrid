from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import json

def index_articles():
    """Load articles, embed them, and store in FAISS."""
    with open("scraped_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    texts = [article["content"] for article in articles]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings)

    vectorstore.save_local("faiss_index")
    print(f"✅ Indexed {len(articles)} articles in FAISS.")

if __name__ == "__main__":
    index_articles()
