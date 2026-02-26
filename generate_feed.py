"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Verified Version for Wix Catalog V3 API
"""

import os
import csv
import re
import requests
from datetime import datetime

# Environment Variables from GitHub Secrets
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
    # MANDATORY for V3: Explicitly request fields or they return as None
    # We request 'variants' as it's the new source for price and stock in V3
    payload = {
        "query": {
            "cursorPaging": {"limit": 100},
            "fields": ["name", "slug", "description", "media", "variants"]
        }
    }
    response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json().get("products", [])

def get_v3_data(product):
    # Wix V3 treats all products as having variants. 
    # Products without choices have a single 'default variant'.
    variants = product.get("variants", [])
    first_variant = variants[0].get("variant", {}) if variants else {}
    
    # 1. PRICE: Extract from actualPrice inside the variant
    price_info = first_variant.get("price", {})
    actual_price = price_info.get("actualPrice", {})
    price = actual_price.get("amount", "0.00")
    currency = actual_price.get("currency", "USD")
    
    # 2. STOCK: Extract from inventoryStatus inside the variant
    inventory = first_variant.get("inventory", {})
    status = inventory.get("availabilityStatus", "")
    
    # Meta requires 'in stock' or 'out of stock'
    availability = "in stock" if status == "IN_STOCK" else "out of stock"
    
    return f"{float(price):.2f} {currency}", availability

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
        # Ensures header is on line 1 for Meta compatibility
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        # Adds a timestamp at the very end to force Git to detect a change
        f.write(f"\n# Updated: {datetime.now().isoformat()}")

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    generate()
    print("Feed generation complete.")
