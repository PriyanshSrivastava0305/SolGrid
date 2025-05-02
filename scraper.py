import os
import fitz  # PyMuPDF
import pandas as pd
import re

# 📁 Folder where your PDF files are stored
pdf_folder = 'C:/Users/KIIT01/Documents/solgrid/pdf'  # Update if your folder path is different

# 📤 Function to extract text from a single PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

# 🧹 Clean and attempt to structure extracted text
def clean_and_structure_text(text, filename):
    cleaned_text = text.lower()
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', cleaned_text)  # remove special characters
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()     # remove extra spaces

    # 🏷 Attempt to infer company and project
    company = None
    project = None

    known_companies = ['adani', 'renew', 'tata power', 'azure', 'ntpc']
    for name in known_companies:
        if name in cleaned_text:
            company = name
            break

    # Try to infer project by looking for key phrases
    match = re.search(r'project(?:\s+name)?\s*:\s*(.+?)(?:\s{2,}|\n|$)', text, re.IGNORECASE)
    if match:
        project = match.group(1).strip()

    return {
        'source': filename,
        'company': company,
        'project': project,
        'cleaned_text': cleaned_text
    }

# 💾 Save data to CSV
def save_to_csv(data, filename):
    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"✅ Data saved to {filename}")
    except PermissionError:
        print(f"❌ Permission denied: Close the file {filename} and try again.")

# 🚀 Main function
def scrape_and_clean_pdfs():
    raw_data = []
    structured_data = []

    for filename in os.listdir(pdf_folder):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, filename)
            print(f"🔍 Extracting from: {filename}")
            text = extract_text_from_pdf(pdf_path)

            raw_data.append({
                'source': filename,
                'text': text
            })

            structured = clean_and_structure_text(text, filename)
            structured_data.append(structured)

    save_to_csv(raw_data, 'pdf_raw_data.csv')
    save_to_csv(structured_data, 'pdf_cleaned_data.csv')

# 🧪 Run it
scrape_and_clean_pdfs()
