import requests
from bs4 import BeautifulSoup
import json

def scrape_articles(base_url="https://en.wikipedia.org/wiki/Large_language_model", num_pages=3):
    """Scrape news articles and save as JSON."""
    articles = []

    for i in range(1, num_pages + 1):
        url = f"{base_url}?page={i}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.find_all("div", class_="article"):
            title = article.find("h2").text.strip()
            content = article.find("p").text.strip()
            articles.append({"title": title, "content": content})

    # Save to JSON
    with open("scraped_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    print(f"✅ Scraped {len(articles)} articles and saved to scraped_articles.json")

if __name__ == "__main__":
    scrape_articles()
