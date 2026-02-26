"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Version: Optimized for Wix V3 with empty variant arrays
"""

import os
import csv
import re
import json
import requests
from datetime import datetime

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
    # We MUST explicitly request these fields in V3 or they return null
    payload = {
        "query": {
            "fields": ["priceData", "stock", "name", "slug", "description", "media"]
        }
    }
    response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("products", [])

def get_price(product):
    # In Wix V3, priceData contains the 'price' amount
    price_data = product.get("priceData", {})
    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    try:
        return f"{float(price):.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"

def get_availability(product):
    # In Wix V3, stock contains 'inventoryStatus'
    stock = product.get("stock", {})
    status = stock.get("inventoryStatus", "")
    if status in ["IN_STOCK", "PARTIALLY_OUT_OF_STOCK"]:
        return "in stock"
    return "out of stock"

def generate():
    products = fetch_all_products()
    rows = []
    for p in products:
        desc = re.sub(r"<[^>]+>", "", p.get("description", "")).strip()
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": desc[:9999] if desc else p.get("name"),
            "availability": get_availability(p),
            "condition": "new",
            "price": get_price(p),
            "link": f"https://www.lakeerieclothing.com/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": "Lake Erie Clothing Company",
            "google_product_category": "Apparel & Accessories > Clothing"
        })
        
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        # We add a timestamp comment so GitHub ALWAYS sees a file change
        f.write(f"# Generated at: {datetime.now().isoformat()}\n")
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    generate()
    print("Feed generation complete.")
