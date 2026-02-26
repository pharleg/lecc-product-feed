"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Complete Version: Explicit V3 Field Requests
"""

import os
import csv
import re
import json
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

BRAND = "Lake Erie Clothing Company"
STORE_BASE_URL = "https://www.lakeerieclothing.com"
GOOGLE_CATEGORY = "Apparel & Accessories > Clothing"


def fetch_all_products():
    products = []
    cursor = None

    while True:
        # MANDATORY: Explicitly request fields or V3 returns null/None
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
    # Try top-level priceData first
    price_data = product.get("priceData", {})
    
    # Fallback to the first variant if top-level is empty
    if not price_data.get("price"):
        variants = product.get("variants", [])
        if variants:
            price_data = variants[0].get("variant", {}).get("priceData", {})

    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    
    try:
        return f"{float(price):.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"


def get_availability(product):
    # Try top-level stock first
    stock = product.get("stock", {})
    
    # Fallback to variant stock
    if not stock.get("inventoryStatus"):
        variants = product.get("variants", [])
        if variants:
            stock = variants[0].get("variant", {}).get("stock", {})

    status = stock.get("inventoryStatus", "")
    
    if status == "IN_STOCK" or status == "PARTIALLY_OUT_OF_STOCK":
        return "in stock"
    return "out of stock"


def build_feed_rows(products):
    rows = []
    for product in products:
        title = product.get("name", "")
        description = product.get("description", "")
        # Strip HTML for Meta compatibility
        description = re.sub(r"<[^>]+>", "", description).strip()
        description = description[:9999] if description else title

        rows.append({
            "id": product.get("id", ""),
            "title": title,
            "description": description,
            "availability": get_availability(product),
            "condition": "new",
            "price": get_price(product),
            "link": f"{STORE_BASE_URL}/product-page/{product.get('slug', '')}",
            "image_link": product.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": BRAND,
            "google_product_category": GOOGLE_CATEGORY,
        })
    return rows


def write_csv(rows, output_path="feed.csv"):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Feed written to {output_path} ({len(rows)} products)")


def main():
    print("Starting LECC Meta product feed generation...")
    products = fetch_all_products()
    rows = build_feed_rows(products)
    write_csv(rows)
    print("Done!")


if __name__ == "__main__":
    main()
