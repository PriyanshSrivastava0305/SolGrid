import requests
from bs4 import BeautifulSoup

def scrape_hyperlinks():
    url = "https://www.nsefi.in/nsefi-news/"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    # Find all "Read More" buttons and extract their hyperlinks
    links = []
    for a_tag in soup.find_all("a", string="READ MORE"):
        href = a_tag.get("href")
        if href:
            links.append(href)

    # Write the hyperlinks to a text file
    with open("read_more_links.txt", "w") as file:
        for link in links:
            file.write(link + "\n")

    print(f"Successfully saved {len(links)} links to 'read_more_links.txt'.")

if __name__ == "__main__":
    scrape_hyperlinks()