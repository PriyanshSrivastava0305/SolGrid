import requests
from bs4 import BeautifulSoup
import json
import time

def clean_text(text):
    return ' '.join(text.strip().split())

def extract_article_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find("div", class_="blog_detail_content")
        if not content_div:
            print(f"❌ Skipping {url} - content div not found.")
            return None

        title_tag = content_div.find("h4")
        date_tag = content_div.find("p").find("i")
        paragraphs = content_div.find_all("p")

        if not title_tag or not date_tag or len(paragraphs) < 2:
            print(f"⚠️ Incomplete data in {url}")
            return None

        title = clean_text(title_tag.text)
        date = clean_text(date_tag.text)
        # Content should be from second <p> tag onwards (skip date para)
        content_parts = [clean_text(p.get_text()) for p in paragraphs[1:]]
        content = ' '.join(content_parts)

        return {
            "title": title,
            "date": date,
            "content": content,
            "url": url
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

def scrape_all_links(txt_file, output_json):
    with open(txt_file, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f.readlines() if line.strip()]

    all_articles = []

    for idx, link in enumerate(links):
        print(f"🔍 Scraping {idx + 1}/{len(links)}: {link}")
        article = extract_article_data(link)
        if article:
            all_articles.append(article)
        time.sleep(0.5)  # polite scraping

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"✅ Done. Saved {len(all_articles)} articles to {output_json}")

if __name__ == "__main__":
    scrape_all_links("article_links.txt", "scraped_articles.json")
