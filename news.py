import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up the Chrome driver with webdriver_manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def scrape_articles():
    # Step 1: Open the homepage
    url = "https://www.nsefi.in/nsefi-news/"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Step 2: Find the "read more" links
    articles = driver.find_elements(By.CSS_SELECTOR, "figure .fusion-post-title a")

    # Debugging: Print the number of articles found
    print(f"Found {len(articles)} 'read more' article links.")
    
    # If no articles are found, print the links on the page
    if len(articles) == 0:
        print(driver.page_source)  # Print the full page source for inspection
    
    article_links = [article.get_attribute('href') for article in articles]
    
    # Debugging: Print the first few article links
    print("First few article links:")
    for link in article_links[:5]:  # Print first 5 links for debugging
        print(link)

    # Step 3: Extract data from each article
    data = []
    for link in article_links:
        driver.get(link)
        time.sleep(5)  # Allow the article page to load
        
        # Get article content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Debugging: Print the page title to check if we're on the correct page
        title = soup.find('h1', class_='entry-title').text.strip() if soup.find('h1', class_='entry-title') else 'No title'
        print(f"Scraping article: {title}")
        
        date = soup.find('time', class_='entry-date').text.strip() if soup.find('time', class_='entry-date') else 'No date'
        content = soup.find('div', class_='entry-content').text.strip() if soup.find('div', class_='entry-content') else 'No content'

        # Add the article to data
        data.append([title, date, content])

        # Print progress for each article
        print(f"Article scraped: {title}")
        
    # Step 4: Save the data to CSV
    if data:
        df = pd.DataFrame(data, columns=["Title", "Date", "Content"])
        df.to_csv("nsefi_articles.csv", index=False)
        print("Articles have been saved to 'nsefi_articles.csv'.")
    else:
        print("No articles to save.")

    # Step 5: Close the driver
    driver.quit()

# Run the scraper
scrape_articles()
