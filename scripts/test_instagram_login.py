"""
Test script to perform Instagram login with Playwright.
Tests the exact selectors and actions needed for the workflow.
"""

import asyncio
from playwright.async_api import async_playwright


async def test_instagram_login():
    """Test Instagram login flow."""
    async with async_playwright() as p:
        # Launch browser with custom profile (same as workflow)
        print("Launching browser with persistent profile and anti-detection...")
        context = await p.chromium.launch_persistent_context(
            "C:/BrowserProfiles/instagram",
            headless=False,
            channel="chrome",
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-extensions",
                "--disable-popup-blocking",
                "--disable-translate",
                "--disable-sync",
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--use-mock-keychain",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ],
            ignore_default_args=[
                "--enable-automation",
                "--enable-blink-features=IdleDetection",
            ],
            viewport={"width": 1920, "height": 1080},
        )

        # Get or create page
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()

        # Inject anti-detection script
        print("Injecting anti-detection JavaScript...")
        await context.add_init_script("""
            // Override navigator.webdriver to hide automation
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // Override navigator.plugins to look like a real browser
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', filename: 'internal-nacl-plugin'}
                ],
                configurable: true
            });

            // Override navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });

            // Remove automation-related properties from window
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)

        print("Navigating to Instagram login page...")
        await page.goto(
            "https://www.instagram.com/accounts/login/",
            wait_until="domcontentloaded",
        )

        # Wait for page to load
        print("Waiting for page to load...")
        await asyncio.sleep(3)

        # Check if already logged in (look for feed or profile elements)
        try:
            # Check if we're redirected to home (already logged in)
            if "/accounts/login" not in page.url:
                print(f"Already logged in! Current URL: {page.url}")
                await context.close()
                return
        except Exception:
            pass

        # Wait for login form
        print("Checking for login form...")
        try:
            await page.wait_for_selector(
                "input[name='username']", state="visible", timeout=10000
            )
            print("Login form found!")
        except Exception as e:
            print(f"Login form not found: {e}")
            print(f"Current URL: {page.url}")
            # Take screenshot
            await page.screenshot(path="C:/BrowserProfiles/instagram_error.png")
            print("Screenshot saved to instagram_error.png")
            await context.close()
            return

        # Type username
        print("Typing username...")
        username_input = await page.query_selector("input[name='username']")
        if username_input:
            await username_input.click()  # Click to focus
            await asyncio.sleep(0.5)
            await username_input.fill("")  # Clear first
            await username_input.type("omer.okumuss", delay=100)  # Slower typing
            print("Username typed!")
        else:
            print("Username input not found!")

        await asyncio.sleep(1)

        # Type password
        print("Typing password...")
        password_input = await page.query_selector("input[name='password']")
        if password_input:
            await password_input.click()  # Click to focus
            await asyncio.sleep(0.5)
            await password_input.fill("")  # Clear first
            await password_input.type("6729Raumafu.", delay=100)  # Slower typing
            print("Password typed!")
        else:
            print("Password input not found!")

        await asyncio.sleep(2)

        # Take screenshot before clicking login
        await page.screenshot(path="C:/BrowserProfiles/before_login.png")
        print("Screenshot saved: before_login.png")

        # Click login button
        print("Clicking login button...")
        login_button = await page.query_selector("button[type='submit']")
        if login_button:
            # Check if button is enabled
            is_disabled = await login_button.get_attribute("disabled")
            print(f"Login button disabled: {is_disabled}")
            await login_button.click()
            print("Login button clicked!")
        else:
            print("Login button not found!")

        # Wait for login to complete (longer wait)
        print("Waiting for login to complete (15 seconds)...")
        await asyncio.sleep(15)

        # Take screenshot after login attempt
        await page.screenshot(path="C:/BrowserProfiles/after_login.png")
        print("Screenshot saved: after_login.png")

        # Check result
        print(f"\nFinal URL: {page.url}")

        # Look for error messages
        print("\nChecking for error messages...")

        # Try various error selectors
        error_selectors = [
            "[role='alert']",
            "#slfErrorAlert",
            "p[data-testid='login-error-message']",
            "div[class*='error']",
            "span[class*='error']",
        ]

        for sel in error_selectors:
            error_el = await page.query_selector(sel)
            if error_el:
                error_text = await error_el.text_content()
                print(f"Error found ({sel}): {error_text}")

        # Check page content for any error text
        page_text = await page.text_content("body")
        if (
            "Sorry" in page_text
            or "incorrect" in page_text.lower()
            or "wrong" in page_text.lower()
        ):
            print("Page contains error-related text")
            # Find the specific text
            import re

            matches = re.findall(
                r".{0,50}(sorry|incorrect|wrong|error).{0,50}", page_text.lower()
            )
            for match in matches[:3]:
                print(f"  Context: ...{match}...")

        if "/accounts/login" not in page.url:
            print("\nSUCCESS! Login appears successful.")

            # Navigate to profile
            print("\nNavigating to profile page...")
            await page.goto(
                "https://www.instagram.com/omer.okumuss/",
                wait_until="domcontentloaded",
            )
            await asyncio.sleep(5)

            print(f"Profile page URL: {page.url}")

            # Check for posts
            posts = await page.query_selector_all("a[href*='/p/']")
            print(f"Found {len(posts)} post links")

            # Get images
            images = await page.query_selector_all("img[src*='cdninstagram']")
            print(f"Found {len(images)} Instagram images")
        else:
            print("\nLogin failed - still on login page")

        print("\nKeeping browser open for 60 seconds for manual inspection...")
        await asyncio.sleep(60)

        await context.close()


if __name__ == "__main__":
    asyncio.run(test_instagram_login())
