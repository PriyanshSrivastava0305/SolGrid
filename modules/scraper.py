import requests
from bs4 import BeautifulSoup

def geocode_location(location):
    api_key = "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"
    url = f"https://api.groq.com/v1/geocode?query={location}&key={api_key}"
    response = requests.get(url)
    print(f"Geocoding response for {location}: {response.status_code}, {response.text}")  # Debug

    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            lat = data["results"][0]["geometry"]["lat"]
            lon = data["results"][0]["geometry"]["lng"]
            return lat, lon
    return None, None

def scrape_mnre():
    url = "https://mnre.gov.in/solar"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    projects = []
    for project in soup.find_all("div", class_="project"):  # Adjust based on actual HTML structure
        name = project.find("h3").text.strip()
        capacity = project.find("span", class_="capacity").text.strip()
        location = project.find("span", class_="location").text.strip()
        projects.append({"name": name, "capacity": capacity, "location": location})
    return projects

def scrape_seci():
    url = "https://www.seci.co.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    projects = []
    for project in soup.find_all("div", class_="project"):  # Adjust based on actual HTML structure
        name = project.find("h3").text.strip()
        capacity = project.find("span", class_="capacity").text.strip()
        location = project.find("span", class_="location").text.strip()
        projects.append({"name": name, "capacity": capacity, "location": location})
    return projects

def scrape_data():
    projects = [
        {"name": "Project A", "capacity": "100 MW", "location": "Delhi"},
        {"name": "Project B", "capacity": "200 MW", "location": "Mumbai"}
    ]

    for project in projects:
        lat, lon = geocode_location(project["location"])
        project["latitude"] = lat
        project["longitude"] = lon

    print(projects)  # Debug: Print the scraped data
    return projects