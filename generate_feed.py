"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Corrected Version for Wix V3 API
"""

import os
import csv
import re
import requests

WIX_API_KEY = os.environ["WIX_API_KEY"]
WIX_SITE_ID = os.environ["WIX_SITE_ID"]
WIX_ACCOUNT_ID = os.environ["WIX_ACCOUNT_ID"]
WIX_API_URL = "https://www.wixapis.com/stores/v3/products/query"

HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "wix-account-id": WIX_ACCOUNT_ID,
    "Content-Type": "application/json",
}

FEED_COLUMNS = [
    "id", "title", "description", "availability", "condition",
    "price", "link", "image_link", "brand", "google_product_category",
]

def fetch_all_products():
    # We must explicitly request 'variants' and 'media' fields in V3
    payload = {
        "query": {
            "fields": ["name", "slug", "description", "media", "variants"]
        }
    }
    response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json().get("products", [])

def get_v3_data(product):
    # Wix V3 stores price and stock in the 'variants' array
    variants = product.get("variants", [])
    first_variant = variants[0].get("variant", {}) if variants else {}
    
    # Extract Price
    price_info = first_variant.get("price", {})
    price = price_info.get("actualPrice", {}).get("amount", "0.00")
    currency = price_info.get("actualPrice", {}).get("currency", "USD")
    
    # Extract Stock Status
    stock_info = first_variant.get("stock", {})
    status = stock_info.get("inventoryStatus", "OUT_OF_STOCK")
    availability = "in stock" if status == "IN_STOCK" else "out of stock"
    
    return f"{price} {currency}", availability

def generate():
    products = fetch_all_products()
    rows = []
    for p in products:
        price, availability = get_v3_data(p)
        desc = re.sub(r"<[^>]+>", "", p.get("description", "")).strip()
        
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": desc[:9999] or p.get("name"),
            "availability": availability,
            "condition": "new",
            "price": price,
            "link": f"https://www.lakeerieclothing.com/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": "Lake Erie Clothing Company",
            "google_product_category": "Apparel & Accessories > Clothing"
        })
        
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    generate()
    print("Feed generation complete.")
