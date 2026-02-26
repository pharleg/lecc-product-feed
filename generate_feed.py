"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Corrected Version for Wix Catalog V3 API
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
    products = []
    cursor = None

    while True:
        # MANDATORY: Explicitly request 'variantsInfo' in the fields array for V3
        payload = {
            "query": {
                "cursorPaging": {"limit": 100},
                "fields": ["name", "slug", "description", "media", "variantsInfo"]
            }
        }
        if cursor:
            payload["query"]["cursorPaging"]["cursor"] = cursor

        response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()

        batch = data.get("products", [])
        products.extend(batch)
        print(f"Fetched {len(batch)} products")

        next_cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
        if not next_cursor or len(batch) == 0:
            break
        cursor = next_cursor

    return products

def get_v3_data(product):
    # Wix V3 stores price and stock in variantsInfo.variants
    variants_info = product.get("variantsInfo", {})
    variants = variants_info.get("variants", [])
    
    # Use the first variant for default price and stock
    first_variant = variants[0] if variants else {}
    
    # V3 Price Path: price -> actualPrice -> amount
    price_obj = first_variant.get("price", {})
    actual_price = price_obj.get("actualPrice", {})
    price = actual_price.get("amount", "0.00")
    currency = actual_price.get("currency", "USD")
    
    # V3 Stock Path: inventory -> availabilityStatus
    inventory = first_variant.get("inventory", {})
    status = inventory.get("availabilityStatus", "")
    
    # Map V3 status to Meta requirements
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
        # Header must be row 1 for Meta compatibility
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        # Add timestamp at very end to force Git update without breaking columns
        f.write(f"\n# Feed Updated: {datetime.now().isoformat()}")

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    generate()
    print("Feed generation complete.")
