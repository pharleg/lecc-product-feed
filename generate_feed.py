"""
Lake Erie Clothing Company - Meta Product Feed Generator
Fetches products from Wix Stores Catalog V3 API and generates a Meta-compatible CSV feed.
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
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text[:2000]}")
        response.raise_for_status()
        data = response.json()

        if not products and data.get("products"):
            p = data["products"][0]
            print("=== PRICE FIELDS ===")
            print(json.dumps({k: v for k, v in p.items() if "price" in k.lower() or "Price" in k}, indent=2))
            print("=== STOCK FIELDS ===")
            print(json.dumps({k: v for k, v in p.items() if "stock" in k.lower() or "inventor" in k.lower() or "availab" in k.lower()}, indent=2))

        batch = data.get("products", [])
        products.extend(batch)
        print(f"Fetched {len(batch)} products")

        next_cursor = data.get("pagingMetadata", {}).get("cursors", {}).get("next")
        if not next_cursor or len(batch) == 0:
            break
        cursor = next_cursor

    print(f"Total products fetched: {len(products)}")
    return products


def get_product_url(product):
    slug = product.get("slug", "")
    return f"{STORE_BASE_URL}/product-page/{slug}" if slug else ""


def get_main_image(product):
    media = product.get("media", {})
    main = media.get("main", {})
    image = main.get("image", {})
    return image.get("url", "")


def get_price(product):
    price_data = product.get("priceData", product.get("price", {}))
    price = price_data.get("price", price_data.get("formatted", {}).get("price", "0"))
    currency = price_data.get("currency", "USD")
    try:
        return f"{float(price):.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"


def get_availability(product):
    stock = product.get("stock", {})
    in_stock = stock.get("inStock", stock.get("availability") == "IN_STOCK")
    return "in stock" if in_stock else "out of stock"


def build_feed_rows(products):
    rows = []
    for product in products:
        product_id = product.get("id", "")
        title = product.get("name", "")
        description = product.get("description", "")
        description = re.sub(r"<[^>]+>", "", description).strip()
        description = description[:9999] if description else title

        row = {
            "id": product_id,
            "title": title,
            "description": description,
            "availability": get_availability(product),
            "condition": "new",
            "price": get_price(product),
            "link": get_product_url(product),
            "image_link": get_main_image(product),
            "brand": BRAND,
            "google_product_category": GOOGLE_CATEGORY,
        }
        rows.append(row)
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
