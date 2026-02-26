"""
Lake Erie Clothing Company - Meta Product Feed Generator
Fetches products from Wix Stores API and generates a Meta-compatible CSV feed.
"""

import os
import csv
import re
import requests

WIX_API_KEY = os.environ["WIX_API_KEY"]
WIX_SITE_ID = os.environ["WIX_SITE_ID"]
WIX_ACCOUNT_ID = os.environ["WIX_ACCOUNT_ID"]

WIX_API_URL = "https://www.wixapis.com/stores/v1/products/query"

HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "wix-account-id": WIX_ACCOUNT_ID,
    "Content-Type": "application/json",
}

# Meta required CSV columns
FEED_COLUMNS = [
    "id",
    "title",
    "description",
    "availability",
    "condition",
    "price",
    "link",
    "image_link",
    "brand",
    "google_product_category",
]

BRAND = "Lake Erie Clothing Company"
STORE_BASE_URL = "https://www.lakeerieclothing.com"
GOOGLE_CATEGORY = "Apparel & Accessories > Clothing"


def fetch_all_products():
    """Fetch all products from Wix Stores API with pagination."""
    products = []
    offset = 0
    limit = 100

    while True:
        payload = {
            "query": {
                "paging": {"limit": limit, "offset": offset},
            }
        }

        print(f"Sending request to: {WIX_API_URL}")
        print(f"Headers (redacted key): wix-site-id={WIX_SITE_ID}, wix-account-id={WIX_ACCOUNT_ID}")
        response = requests.post(WIX_API_URL, headers=HEADERS, json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:1000]}")
        response.raise_for_status()
        data = response.json()

        batch = data.get("products", [])
        products.extend(batch)
        print(f"Fetched {len(batch)} products (offset {offset})")

        total = data.get("metadata", {}).get("total", 0)
        offset += limit
        if offset >= total or len(batch) == 0:
            break

    print(f"Total products fetched: {len(products)}")
    return products


def get_product_url(product):
    slug = product.get("slug", "")
    return f"{STORE_BASE_URL}/product-page/{slug}" if slug else ""


def get_main_image(product):
    media = product.get("media", {})
    main_media = media.get("mainMedia", {})
    image = main_media.get("image", {})
    return image.get("url", "")


def get_price(product):
    price_data = product.get("priceData", {})
    price = price_data.get("price", 0)
    currency = price_data.get("currency", "USD")
    return f"{float(price):.2f} {currency}"


def get_availability(product):
    inventory = product.get("stock", {})
    in_stock = inventory.get("inStock", False)
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
