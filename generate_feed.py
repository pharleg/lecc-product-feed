"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Version: Explicit Field Requests and Variant Fallbacks for Wix V3
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
        # We explicitly request 'priceData', 'stock', and 'variants' 
        # as V3 often returns them as null unless specifically asked for.
        payload = {
            "query": {
                "cursorPaging": {"limit": 100},
                "fields": ["priceData", "stock", "variants", "name", "slug", "description", "media"]
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

    print(f"Total products fetched: {len(products)}")
    return products

def get_price(product):
    # 1. Try top-level priceData
    price_data = product.get("priceData")
    
    # 2. Fallback to the first variant (required for many V3 products)
    if not price_data:
        variants = product.get("variants", [])
        if variants:
            # Check for nested variant object containing priceData
            price_data = variants[0].get("variant", {}).get("priceData")

    if not price_data:
        return "0.00 USD"

    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    try:
        return f"{float(price):.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"

def get_availability(product):
    # 1. Try top-level stock
    stock = product.get("stock")
    
    # 2. Fallback to the first variant stock
    if not stock:
        variants = product.get("variants", [])
        if variants:
            stock = variants[0].get("variant", {}).get("stock")

    if not stock:
        return "out of stock"

    # Wix V3 uses 'inventoryStatus'
    status = stock.get("inventoryStatus", "")
    if status == "IN_STOCK" or status == "PARTIALLY_OUT_OF_STOCK":
        return "in stock"
    return "out of stock"

def get_main_image(product):
    media = product.get("media", {})
    main = media.get("main", {})
    image = main.get("image", {})
    return image.get("url", "")

def build_feed_rows(products):
    rows = []
    for product in products:
        title = product.get("name", "Untitled Product")
        desc = product.get("description", "")
        # Clean up HTML tags for the feed
        desc = re.sub(r"<[^>]+>", "", desc).strip()
        
        rows.append({
            "id": product.get("id"),
            "title": title,
            "description": desc[:9999] if desc else title,
            "availability": get_availability(product),
            "condition": "new",
            "price": get_price(product),
            "link": f"{STORE_BASE_URL}/product-page/{product.get('slug', '')}",
            "image_link": get_main_image(product),
            "brand": BRAND,
            "google_product_category": GOOGLE_CATEGORY,
        })
    return rows

def write_csv(rows):
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    all_products = fetch_all_products()
    feed_data = build_feed_rows(all_products)
    write_csv(feed_data)
    print(f"Done! Feed generated with {len(feed_data)} products.")
