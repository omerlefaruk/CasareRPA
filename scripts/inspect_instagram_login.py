"""
Script to inspect Instagram login page and get accurate selectors.
Uses Playwright to capture the actual DOM structure.
"""

import asyncio
from playwright.async_api import async_playwright


async def inspect_instagram_login():
    """Inspect Instagram login page and print form selectors."""
    async with async_playwright() as p:
        # Launch browser with custom profile
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        print("Navigating to Instagram login page...")
        await page.goto(
            "https://www.instagram.com/accounts/login/", wait_until="networkidle"
        )

        # Wait for page to fully load
        await asyncio.sleep(3)

        print("\n" + "=" * 60)
        print("INSPECTING INSTAGRAM LOGIN PAGE")
        print("=" * 60)

        # Find all input elements
        print("\n--- INPUT ELEMENTS ---")
        inputs = await page.query_selector_all("input")
        for i, inp in enumerate(inputs):
            name = await inp.get_attribute("name")
            input_type = await inp.get_attribute("type")
            aria_label = await inp.get_attribute("aria-label")
            placeholder = await inp.get_attribute("placeholder")
            autocomplete = await inp.get_attribute("autocomplete")
            print(f"\nInput {i+1}:")
            print(f"  name: {name}")
            print(f"  type: {input_type}")
            print(f"  aria-label: {aria_label}")
            print(f"  placeholder: {placeholder}")
            print(f"  autocomplete: {autocomplete}")

        # Find buttons
        print("\n--- BUTTON ELEMENTS ---")
        buttons = await page.query_selector_all("button")
        for i, btn in enumerate(buttons):
            btn_type = await btn.get_attribute("type")
            text = await btn.text_content()
            disabled = await btn.get_attribute("disabled")
            print(f"\nButton {i+1}:")
            print(f"  type: {btn_type}")
            print(f"  text: {text.strip() if text else 'N/A'}")
            print(f"  disabled: {disabled}")

        # Try specific selectors
        print("\n--- TESTING SELECTORS ---")

        # Username field selectors to try
        username_selectors = [
            "input[name='username']",
            "input[aria-label='Phone number, username, or email']",
            "input[autocomplete='username']",
            "input[type='text']",
        ]

        for sel in username_selectors:
            elem = await page.query_selector(sel)
            print(f"  {sel}: {'FOUND' if elem else 'NOT FOUND'}")

        # Password field selectors
        password_selectors = [
            "input[name='password']",
            "input[aria-label='Password']",
            "input[autocomplete='current-password']",
            "input[type='password']",
        ]

        for sel in password_selectors:
            elem = await page.query_selector(sel)
            print(f"  {sel}: {'FOUND' if elem else 'NOT FOUND'}")

        # Login button selectors
        button_selectors = [
            "button[type='submit']",
            "button:has-text('Log in')",
            "button:has-text('Log In')",
            "div[role='button']:has-text('Log in')",
        ]

        for sel in button_selectors:
            elem = await page.query_selector(sel)
            print(f"  {sel}: {'FOUND' if elem else 'NOT FOUND'}")

        # Get page HTML for forms
        print("\n--- FORM STRUCTURE ---")
        forms = await page.query_selector_all("form")
        print(f"Found {len(forms)} form(s)")

        for i, form in enumerate(forms):
            form_html = await form.evaluate("el => el.outerHTML.substring(0, 500)")
            print(f"\nForm {i+1} (first 500 chars):")
            print(form_html)

        # Keep browser open for manual inspection
        print("\n" + "=" * 60)
        print("Browser will stay open for 30 seconds for manual inspection.")
        print("=" * 60)
        await asyncio.sleep(30)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_instagram_login())
