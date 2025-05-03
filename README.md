
# SolGrid: Solar Detective

## Mapping India's Solar Infrastructure Using Agentic AI

SolGrid is a comprehensive tool designed to collect, analyze, and visualize data related to India's solar energy infrastructure. Using agentic AI and retrieval-augmented generation (RAG), the system scrapes information from various sources, processes the data, and provides intelligent insights about India's solar capacity and development.

---

## Key Features

- **🌐 Intelligent Data Scraping:** Automatically collects articles and data about India's solar infrastructure from multiple sources  
- **📄 PDF Processing:** Extracts and structures information from PDF documents  
- **🔍 Vector Search:** Uses FAISS and HuggingFace embeddings for semantic search and retrieval  
- **🧠 RAG Implementation:** Leverages LLMs (Llama-3.1-8b) via Groq API to generate insights from collected data  
- **📊 Interactive Visualization:** Streamlit-based dashboard for exploring solar capacity data  
- **📰 Automated News Monitoring:** Tracks developments in India's solar energy sector  

---

## Installation

### Prerequisites

- Python 3.7+
- Required system packages:
  ```sh
  sudo apt-get install libxml2 libxslt1-dev
  ```

### Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/PriyanshSrivastava0305/SolGrid.git
    cd SolGrid
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

---

## Usage

### Data Collection & Processing

| Command                | Action                        | Output                   |
|------------------------|-------------------------------|--------------------------|
| `python news.py`       | Scrape news articles          | `scraped_articles.json`  |
| `python scraper.py`    | Process PDF documents         | Structured text files    |
| `python indexer.py`    | Create vector index           | FAISS index files        |

### Analysis & Visualization

- **Query the RAG system:**
    ```sh
    python rag.py
    ```
    Example questions:
    - "What's India's current solar capacity?"
    - "Compare solar growth in Maharashtra and Rajasthan"

- **Launch dashboard:**
    ```sh
    streamlit run app.py
    ```

---

## Data Insights
 Sample data generated from RAG Agent:

| Year     | Installed Capacity (MW) | Power Generation (GWh) |
|----------|------------------------|------------------------|
| 2019     | 34,900                 | 43,900                 |
| 2020     | 44,130                 | 55,911                 |
| 2021     | 56,960                 | 73,419                 |
| 2022     | 73,080                 | 96,511                 |
| 2023 (P) | 94,180                 | 127,899                |

**Recent milestone:**  
India has achieved 100 GW of solar capacity, becoming the fourth country to do so after the US, China, and Germany.

---

## Project Structure

```
SolGrid/
├── app.py                # Streamlit dashboard
├── scraper.py            # PDF text extraction
├── indexer.py            # Vector embeddings manager
├── rag.py                # RAG system implementation
├── news.py               # Article scraper
├── test.py               # Article scraping tests
├── article_links.txt     # Source URLs for articles
├── scraped_articles.json # Collected article data
├── output.csv            # Processed solar capacity data
├── requirements.txt      # Python dependencies
├── packages.txt          # System dependencies
```

---

## Technologies Used

- **Web Scraping:** BeautifulSoup, Requests
- **Natural Language Processing:** LangChain, HuggingFace Embeddings
- **Vector Database:** FAISS
- **Large Language Models:** Llama 3.1 via Groq API
- **Data Processing:** Pandas, PyMuPDF (Fitz)
- **Data Visualization:** Plotly, Streamlit

---

## Contributors

- Priyansh Srivastava
- Romit Chatterjee
- Krishna Gopal Kar
- Ayushman Pradhan
---
