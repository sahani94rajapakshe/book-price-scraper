import os
import shutil
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

# -----------------------
# Configurations
# -----------------------
BASE_URL = "https://books.toscrape.com/catalogue/category/books_1/page-{}.html"
OUTPUT_FOLDER = "output"
BACKUP_FOLDER = "backup"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# -----------------------
# Setup Folders
# -----------------------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# -----------------------
# Functions
# -----------------------
def backup_old_files():
    """Move old Excel files to backup before creating a new one."""
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith(".xlsx"):
            shutil.move(os.path.join(OUTPUT_FOLDER, file),
                        os.path.join(BACKUP_FOLDER, file))
            print(f"Backed up: {file}")

def scrape_books():
    """Scrape book titles, prices, stock, ratings from all pages."""
    books_data = []
    page_num = 1
    ratings_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    while True:
        url = BASE_URL.format(page_num)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        books = soup.find_all("article", class_="product_pod")
        if not books:
            break

        for book in books:
            title = book.h3.a["title"]
            price_text = book.find("p", class_="price_color").text
            try:
                price = float(price_text.replace("£", "").replace("Â", "").strip())
            except ValueError:
                price = None

            stock = book.find("p", class_="instock availability").text.strip()
            rating_class = book.p.get("class", [])
            rating = ratings_map.get(rating_class[1], None) if len(rating_class) > 1 else None

            books_data.append({
                "Title": title,
                "Price (£)": price,
                "Stock": stock,
                "Rating": rating
            })

        page_num += 1

    return books_data

# -----------------------
# Main Script
# -----------------------
if __name__ == "__main__":
    print("Starting backup...")
    backup_old_files()

    print("Scraping books...")
    books_data = scrape_books()

    if books_data:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = os.path.join(OUTPUT_FOLDER, f"books_{today}.xlsx")

        df = pd.DataFrame(books_data)
        df.to_excel(output_file, index=False)

        print(f"Scraping completed. Data saved to: {output_file}")
    else:
        print("No books scraped. Please check the site or your internet connection.")
