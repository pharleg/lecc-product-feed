"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Version: Corrected V3 Field Selection and Variant Mapping
"""

import os
import csv
import re
import json
import requests

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

BRAND = "Lake Erie Clothing Company"
STORE_BASE_URL = "https://www.lakeerieclothing.com"
GOOGLE_CATEGORY = "Apparel & Accessories > Clothing"

def fetch_all_products():
    products = []
    cursor = None

    while True:
        # MANDATORY: Explicitly request 'variants' and 'priceData' in V3
        payload = {
            "query": {
                "cursorPaging": {"limit": 100},
                "fields": ["name", "slug", "description", "media", "variants", "priceData", "stock"]
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

def get_v3_price_and_stock(product):
    # In V3, pricing and inventory are most reliable at the variant level
    variants = product.get("variants", [])
    # Even simple products have a default variant at index 0
    first_variant = variants[0].get("variant", {}) if variants else {}
    
    # --- Price Logic ---
    # Try variant-level priceData first, then fallback to top-level
    price_data = first_variant.get("priceData") or product.get("priceData") or {}
    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    
    # --- Stock Logic ---
    # Try variant-level stock first, then fallback to top-level
    stock = first_variant.get("stock") or product.get("stock") or {}
    status = stock.get("inventoryStatus", "")
    
    # Meta specific availability strings
    availability = "in stock" if status == "IN_STOCK" else "out of stock"
    
    return f"{float(price):.2f} {currency}", availability

def generate():
    products = fetch_all_products()
    rows = []
    
    for p in products:
        price, availability = get_v3_price_and_stock(p)
        desc = re.sub(r"<[^>]+>", "", p.get("description", "")).strip()
        
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": desc[:9999] or p.get("name"),
            "availability": availability,
            "condition": "new",
            "price": price,
            "link": f"{STORE_BASE_URL}/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": BRAND,
            "google_product_category": GOOGLE_CATEGORY,
        })
        
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    generate()
    print("Feed generation complete.")
