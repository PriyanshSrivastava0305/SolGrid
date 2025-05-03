from modules.scraper import scrape_data

def test_scrape_data():
    data = scrape_data()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "capacity" in data[0]
    assert "location" in data[0]