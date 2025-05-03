from modules.scraper import scrape_data
from modules.database import initialize_database, save_data
from modules.dashboard import create_dashboard

def main():
    # Step 1: Scrape data from online sources
    scraped_data = scrape_data()

    # Step 2: Save data to the database
    db = initialize_database()
    save_data(db, scraped_data)

    # Step 3: Launch the dashboard
    create_dashboard()

if __name__ == "__main__":
    main()