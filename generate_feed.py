"""
Lake Erie Clothing Company - Meta Product Feed Generator
Diagnostic Version: Full Product Dump
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
        payload = {
            "query": {
                "cursorPaging": {"limit": 100},
                # We are requesting every possible field to find where the data is hidden
                "fields": ["priceData", "stock", "variants", "name", "slug", "description", "media", "convertedPriceData"]
            }
        }
        if cursor:
            payload["query"]["cursorPaging"]["cursor"] = cursor

        response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()

        batch = data.get("products", [])
        
        # DIAGNOSTIC: Print the full JSON of the first product
        if not products and batch:
            print("--- FULL RAW PRODUCT DATA (DIAGNOSTIC) ---")
            print(json.dumps(batch[0], indent=2))
            print("--- END DIAGNOSTIC ---")

        products.extend(batch)
        print(f"Fetched {len(batch)} products")

        next_cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
        if not next_cursor or len(batch) == 0:
            break
        cursor = next_cursor

    return products

def get_price(product):
    # Search top-level, then convertedPriceData, then variants
    price_data = product.get("priceData") or product.get("convertedPriceData")
    
    if not price_data:
        variants = product.get("variants", [])
        if variants:
            v_obj = variants[0].get("variant", {})
            price_data = v_obj.get("priceData") or v_obj.get("convertedPriceData")

    if not price_data:
        return "0.00 USD"

    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    try:
        return f"{float(price):.2f} {currency}"
    except:
        return f"0.00 {currency}"

def get_availability(product):
    stock = product.get("stock")
    
    if not stock:
        variants = product.get("variants", [])
        if variants:
            stock = variants[0].get("variant", {}).get("stock")

    if not stock:
        return "out of stock"

    status = stock.get("inventoryStatus", "")
    if status in ["IN_STOCK", "PARTIALLY_OUT_OF_STOCK"]:
        return "in stock"
    return "out of stock"

def build_feed_rows(products):
    rows = []
    for product in products:
        title = product.get("name", "No Title")
        desc = re.sub(r"<[^>]+>", "", product.get("description", "")).strip()
        
        rows.append({
            "id": product.get("id"),
            "title": title,
            "description": desc[:9999] if desc else title,
            "availability": get_availability(product),
            "condition": "new",
            "price": get_price(product),
            "link": f"{STORE_BASE_URL}/product-page/{product.get('slug', '')}",
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
    write_csv(build_feed_rows(prods))
    print(f"Done! Processed {len(prods)} products.")
