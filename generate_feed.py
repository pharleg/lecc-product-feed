"""
Lake Erie Clothing Company - Meta Product Feed Generator
Final Brute-Force Version with Full Data Logging
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

def fetch_all_products():
    payload = {
        "query": {
            "fields": ["priceData", "stock", "variants", "name", "slug", "description", "media", "inventory"]
        }
    }
    response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()
    
    products = data.get("products", [])
    
    # CRITICAL LOGGING: This will show us the REAL structure in GitHub Actions
    if products:
        print("--- RAW API RESPONSE PREVIEW (FIRST ITEM) ---")
        print(json.dumps(products[0], indent=2))
        print("--- END PREVIEW ---")
        
    return products

def get_v3_price(p):
    # Try multiple V3 paths
    price_obj = p.get("priceData") or p.get("convertedPriceData")
    
    # Check inside first variant if top-level is empty
    if not price_obj and p.get("variants"):
        v = p["variants"][0].get("variant", {})
        price_obj = v.get("priceData") or v.get("price")

    if not price_obj:
        return "0.00 USD"
    
    price = price_obj.get("price") or price_obj.get("amount") or 0
    currency = price_obj.get("currency") or "USD"
    return f"{float(price):.2f} {currency}"

def get_v3_stock(p):
    # Check top-level stock or inventory
    stock_obj = p.get("stock") or p.get("inventory")
    
    # Check inside first variant
    if not stock_obj and p.get("variants"):
        v = p["variants"][0].get("variant", {})
        stock_obj = v.get("stock") or v.get("inventory")

    if not stock_obj:
        return "out of stock"

    # Try different Wix status keys
    status = stock_obj.get("inventoryStatus") or stock_obj.get("status") or ""
    if status in ["IN_STOCK", "PARTIALLY_OUT_OF_STOCK", "AVAILABLE"]:
        return "in stock"
    return "out of stock"

def generate():
    products = fetch_all_products()
    rows = []
    for p in products:
        price = get_v3_price(p)
        stock = get_v3_stock(p)
        desc = re.sub(r"<[^>]+>", "", p.get("description", "")).strip()
        
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": desc[:9999] or p.get("name"),
            "availability": stock,
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
    generate()
    print("Process Complete.")
