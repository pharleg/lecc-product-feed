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
    # We are asking for EVERY possible field that could hold price/stock
    payload = {
        "query": {
            "fields": ["priceData", "stock", "variants", "variantsInfo", "inventory"]
        }
    }
    r = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    r.raise_for_status()
    data = r.json()
    prods = data.get("products", [])
    
    if prods:
        print("--- DIAGNOSTIC DATA ---")
        # This will print the first product structure to your logs
        print(json.dumps(prods[0], indent=2))
        
    return prods

def get_price(p):
    # Try the 4 most common Wix V3 price locations
    price_obj = p.get("priceData") or p.get("variantsInfo", {}).get("variants", [{}])[0].get("price")
    if not price_obj and p.get("variants"):
        price_obj = p["variants"][0].get("variant", {}).get("priceData")
    
    val = price_obj.get("price") or price_obj.get("amount") or "0.00"
    cur = price_obj.get("currency") or "USD"
    return f"{float(val):.2f} {cur}"

def get_stock(p):
    # Try the 3 most common Wix V3 stock locations
    stock_obj = p.get("stock") or p.get("inventory") or p.get("variantsInfo", {}).get("variants", [{}])[0].get("inventory")
    status = stock_obj.get("inventoryStatus") or stock_obj.get("availabilityStatus") or ""
    return "in stock" if status in ["IN_STOCK", "AVAILABLE"] else "out of stock"

def run():
    products = fetch_all()
    rows = []
    # This dummy ID forces Git to see a change every single time
    sync_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    for p in products:
        price = get_price(p)
        stock = get_stock(p)
        desc = re.sub(r"<[^>]+>", "", p.get("description", "")).strip()
        
        rows.append({
            "id": p.get("id"),
            "title": p.get("name"),
            "description": f"{desc[:5000]} (Sync:{sync_id})", # Forces file change
            "availability": stock,
            "condition": "new",
            "price": price,
            "link": f"https://www.lakeerieclothing.com/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": "Lake Erie Clothing Company",
            "google_product_category": "Apparel & Accessories > Clothing"
        })
        
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    run()
