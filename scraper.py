import requests
from bs4 import BeautifulSoup
import json

def scrape_mnre(base_url="https://mnre.gov.in"):
    # Send a GET request to the MNRE homepage
    response = requests.get(base_url)
    if response.status_code == 200:
        print("Successfully accessed the MNRE page.")
    else:
        print(f"Failed to access MNRE: {response.status_code}")
        return

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Example: Find all links on the page, especially PDFs
    links = soup.find_all('a', href=True)
    pdf_links = []

    # Filter out links that likely point to PDF files
    for link in links:
        href = link['href']
        # Check if the link ends with '.pdf' and if it starts with 'http' or '/'. If it's a relative link, append the base_url
        if href.endswith('.pdf'):
            if href.startswith('http'):
                pdf_links.append(href)
            else:
                pdf_links.append(base_url + href)

    if pdf_links:
        print("Found the following PDF links:")
        for pdf_link in pdf_links:
            print(f"PDF Link: {pdf_link}")
    else:
        print("No PDF links found on the MNRE page.")

    # Example: Find all headings or any other structured data
    headings = soup.find_all(['h1', 'h2'])
    if headings:
        print("Found the following headings:")
        for heading in headings:
            print(f"{heading.name}: {heading.text.strip()}")
    else:
        print("No headings found on the MNRE page.")

    # Save the PDF links and headings to a JSON file
    data = {
        "pdf_links": pdf_links,
        "headings": [heading.text.strip() for heading in headings]
    }

    with open("scraped_mnre_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Data saved to 'scraped_mnre_data.json'")

if __name__ == "__main__":
    scrape_mnre()
