import requests
from bs4 import BeautifulSoup
import json

def scrape_articles(base_url="https://en.wikipedia.org/wiki/Large_language_model", num_sections=3):
    """Scrape different sections of an article and save as JSON."""
    articles = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    headings = soup.find_all(["h2", "h3", "h4"]) 

    unwanted_titles = ["Contents"]
    
    for heading in headings:
        title = heading.text.strip()

        if any(unwanted_title.lower() in title.lower() for unwanted_title in unwanted_titles):
            continue

        content = ""
        content_section = heading.find_next("p")
        while content_section:
            content += content_section.text.strip() + "\n"
            content_section = content_section.find_next("p") 
        articles.append({"title": title, "content": content})

        if len(articles) >= num_sections:
            break

    with open("scraped_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    print(f"✅ Scraped {len(articles)} sections and saved to scraped_articles.json")

if __name__ == "__main__":
    scrape_articles()
