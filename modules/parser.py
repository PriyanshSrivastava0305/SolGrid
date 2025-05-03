import os
import pdfplumber

def parse_pdfs(scraped_data):
    parsed_data = []

    for item in scraped_data:
        # Extract the file path if the item is a dictionary
        pdf_path = item.get("file_path") if isinstance(item, dict) else item

        # Skip items with no valid file path
        if not pdf_path:
            print(f"Skipping item with missing file_path: {item}")
            continue

        # Make the file path relative to the current directory
        pdf_path = os.path.join(os.getcwd(), pdf_path)

        if not os.path.isfile(pdf_path):
            print(f"File does not exist: {pdf_path}")
            continue

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                # Placeholder logic to extract relevant data
                if "Capacity" in text:
                    capacity = extract_value(text, "Capacity")
                    location = extract_value(text, "Location")
                    parsed_data.append({
                        "capacity": capacity,
                        "location": location,
                        "source": pdf_path
                    })

    return parsed_data

def extract_value(text, key):
    try:
        start = text.index(key) + len(key) + 1
        end = text.index("\n", start)
        return text[start:end].strip()
    except ValueError:
        return None