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
    # Updated logic: Wix V3 provides numeric price in the 'price' field within 'priceData'
    price_data = product.get("priceData",
