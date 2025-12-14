"""
Test script for Hepsiburada DJI Gimbal scraper.
Demonstrates the verified selectors and extraction logic.
Run: python workflows/test_hepsiburada_scraper.py
"""

import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright


# Verified selectors (tested and working)
SELECTORS = {
    "product_card": "[class*='productCard-module_productCardRoot']",
    "product_name": "[class*='title-module_titleText']",
    "product_price": "[class*='price-module_finalPrice']",
    "cookie_accept": "button:has-text('Kabul et')",
}

TARGET_URL = "https://www.hepsiburada.com/dji/gimbal-c-80781000"
OUTPUT_DIR = "./output"
OUTPUT_FILE = (
    f"{OUTPUT_DIR}/hepsiburada_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)


async def scrape_products():
    """Scrape products from Hepsiburada using verified selectors."""
    products = []

    async with async_playwright() as p:
        # Launch browser (non-headless for debugging)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"[1/6] Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)

        print("[2/6] Waiting for page to load...")
        await page.wait_for_timeout(5000)

        # Accept cookies if present
        print("[3/6] Handling cookie consent...")
        try:
            accept_btn = await page.query_selector(SELECTORS["cookie_accept"])
            if accept_btn:
                await accept_btn.click()
                print("    -> Cookie consent accepted")
                await page.wait_for_timeout(1000)
        except Exception:
            print("    -> No cookie banner found")

        # Wait for products
        print("[4/6] Waiting for products to load...")
        await page.wait_for_selector(SELECTORS["product_card"], timeout=30000)

        # Extract products
        print("[5/6] Extracting product data...")
        cards = await page.query_selector_all(SELECTORS["product_card"])
        print(f"    -> Found {len(cards)} product cards")

        for i, card in enumerate(cards):
            product = {"index": i + 1}

            # Extract name
            name_el = await card.query_selector(SELECTORS["product_name"])
            if name_el:
                product["name"] = (await name_el.inner_text()).strip()
            else:
                product["name"] = ""

            # Extract price
            price_el = await card.query_selector(SELECTORS["product_price"])
            if price_el:
                product["price"] = (await price_el.inner_text()).strip()
            else:
                product["price"] = ""

            # Extract link
            link_el = await card.query_selector("a[href]")
            if link_el:
                product["url"] = await link_el.get_attribute("href")
            else:
                product["url"] = ""

            products.append(product)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"    -> Extracted {i + 1}/{len(cards)} products")

        await browser.close()

    return products


def save_to_csv(products: list, filepath: str):
    """Save products to CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "name", "price", "url"])
        writer.writeheader()
        writer.writerows(products)

    print(f"[6/6] Saved {len(products)} products to {filepath}")


def main():
    """Main entry point."""
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("Hepsiburada DJI Gimbal Scraper - Test Run")
    print("=" * 60)
    print(f"Target URL: {TARGET_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

    # Run scraper
    products = asyncio.run(scrape_products())

    # Save to CSV first (most important)
    print("\n" + "=" * 60)
    save_to_csv(products, OUTPUT_FILE)

    # Display sample
    print("\n" + "=" * 60)
    print("SAMPLE DATA (First 5 Products)")
    print("=" * 60)
    for p in products[:5]:
        name = p["name"][:50].encode("ascii", "replace").decode("ascii")
        print(f"\n#{p['index']}: {name}...")
        print(f"    Price: {p['price']}")

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE!")
    print(f"Total products: {len(products)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
