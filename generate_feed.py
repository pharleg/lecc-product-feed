"""
Lake Erie Clothing Company - Meta Product Feed Generator
Corrected for Wix Catalog V3 API
"""

import os
import csv
import re
import json
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

BRAND = "Lake Erie Clothing Company"
STORE_BASE_URL = "https://www.lakeerieclothing.com"
GOOGLE_CATEGORY = "Apparel & Accessories > Clothing"

def fetch_all_products():
    products = []
    cursor = None
    while True:
        payload = {"query": {"cursorPaging": {"limit": 100}}}
        if cursor:
            payload["query"]["cursorPaging"]["cursor"] = cursor
        response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # This will now definitely show in your GitHub Action Logs
        if not products and data.get("products"):
            p = data["products"][0]
            print("--- DEBUG: API DATA PREVIEW ---")
            print(f"Price Data: {p.get('priceData')}")
            print(f"Stock Data: {p.get('stock')}")

        batch = data.get("products", [])
        products.extend(batch)
        print(f"Fetched {len(batch)} products")
        next_cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
        if not next_cursor or len(batch) == 0:
            break
        cursor = next_cursor
    return products

def get_price(product):
    # Wix V3 path: priceData -> price
    price_data = product.get("priceData", {})
    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    try:
        return f"{float(price):.2f} {currency}"
    except:
        return f"0.00 {currency}"

def get_availability(product):
    # Wix V3 path: stock -> inventoryStatus
    stock = product.get("stock", {})
    status = stock.get("inventoryStatus", "")
    if status == "IN_STOCK" or status == "PARTIALLY_OUT_OF_STOCK":
        return "in stock"
    return "out of stock"

def build_feed_rows(products):
    rows = []
    for product in products:
        desc = re.sub(r"<[^>]+>", "", product.get("description", "")).strip()
        rows.append({
            "id": product.get("id"),
            "title": product.get("name"),
            "description": desc[:9999] if desc else product.get("name"),
            "availability": get_availability(product),
            "condition": "new",
            "price": get_price(product),
            "link": f"{STORE_BASE_URL}/product-page/{product.get('slug')}",
            "image_link": product.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
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
    prods = fetch_all_products()
    rows = build_feed_rows(prods)
    write_csv(rows)
    print(f"Done! Created feed with {len(rows)} products.")
