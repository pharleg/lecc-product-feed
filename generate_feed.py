import os, csv, re, json, requests
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

def fetch_all():
    # We use a broad field request to ensure everything is captured
    payload = {
        "query": {
            "fields": ["name", "slug", "description", "media", "inventory", "actualPriceRange"]
        }
    }
    r = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    r.raise_for_status()
    data = r.json()
    return data.get("products", [])

def get_price(p):
    # Based on your logs, the price is in actualPriceRange -> minValue -> amount
    price_range = p.get("actualPriceRange", {})
    min_val = price_range.get("minValue", {})
    amount = min_val.get("amount", "0.00")
    
    # Currency usually defaults to USD if not found, but we'll try to find it
    currency = min_val.get("currency", "USD")
    
    try:
        return f"{float(amount):.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 USD"

def get_stock(p):
    # Based on your logs, stock is in inventory -> availabilityStatus
    inventory = p.get("inventory", {})
    status = inventory.get("availabilityStatus", "")
    
    if status == "IN_STOCK":
        return "in stock"
    return "out of stock"

def run():
    products = fetch_all()
    rows = []
    
    # Sync ID ensures the file content is unique every time to force GitHub to update
    sync_id = datetime.now().strftime("%Y%m%d%H%M")
    
    for p in products:
        price_str = get_price(p)
        stock_str = get_stock(p)
        
        # Clean description
        desc = p.get("description", "")
        if not desc:
            desc = p.get("name", "")
        desc = re.sub(r"<[^>]+>", "", desc).strip()
        
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": f"{desc[:5000]}", 
            "availability": stock_str,
            "condition": "new",
            "price": price_str,
            "link": f"https://www.lakeerieclothing.com/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": "Lake Erie Clothing Company",
            "google_product_category": "Apparel & Accessories > Clothing",
            "sync_id": sync_id # This column forces a file change so Git commits it
        })
        
    if not rows:
        print("No products found to write.")
        return

    fieldnames = list(rows[0].keys())
    
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Starting LECC Meta product feed generation...")
    run()
    print("Process Complete.")
