import os, csv, re, requests, json
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

def fetch_products():
    # Explicitly request variant data where V3 stores price/stock
    payload = {"query": {"fields": ["variants", "name", "slug", "description", "media"]}}
    response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()
    
    # FORCED DIAGNOSTIC: This will show up in your GitHub Action Logs
    if data.get("products"):
        print("--- DEBUG: FIRST PRODUCT RAW VARIANT DATA ---")
        print(json.dumps(data["products"][0].get("variants", [])[:1], indent=2))
        
    return data.get("products", [])

def get_v3_data(product):
    # Wix V3 treats all products as having at least one variant
    variants = product.get("variants", [])
    first_variant = variants[0].get("variant", {}) if variants else {}
    
    # Extract Price
    price_info = first_variant.get("price", {})
    price = price_info.get("actualPrice", {}).get("amount", "0.00")
    
    # Extract Stock Status
    stock_info = first_variant.get("stock", {})
    status = stock_info.get("inventoryStatus", "OUT_OF_STOCK")
    availability = "in stock" if status == "IN_STOCK" else "out of stock"
    
    return price, availability

def generate():
    products = fetch_products()
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
            "price": f"{price} USD",
            "link": f"https://www.lakeerieclothing.com/product-page/{p.get('slug')}",
            "image_link": p.get("media", {}).get("main", {}).get("image", {}).get("url", ""),
            "brand": "Lake Erie Clothing Company",
            "google_product_category": "Apparel & Accessories > Clothing"
        })
        
    with open("feed.csv", "w", newline="", encoding="utf-8") as f:
        # ADD A TIMESTAMP COMMENT to force Git to see a 'change' every run
        f.write(f"# Updated: {datetime.now().isoformat()}\n")
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    generate()
    print("Feed generation complete.")
