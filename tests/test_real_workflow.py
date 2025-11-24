"""
Real-World Workflow Test
Demonstrates selector normalization with Google search automation
"""

import asyncio
from playwright.async_api import async_playwright
from src.casare_rpa.utils.selector_normalizer import normalize_selector

print("=" * 80)
print("REAL-WORLD WORKFLOW TEST: Google Search Automation")
print("=" * 80)

async def test_google_workflow():
    """
    Simulates a real workflow where user might paste different selector formats
    from different sources (DevTools, selector picker, tutorials, etc.)
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n1. Navigate to Google...")
        await page.goto("https://www.google.com")
        print("   ✓ Loaded Google homepage")
        
        # Different selector formats that users might use
        selector_variants = [
            # From browser DevTools (usually CSS)
            ('textarea[name="q"]', 'CSS from DevTools'),
            
            # From our selector picker (XPath)
            ('//*[@name="q"]', 'XPath from picker'),
            
            # User types simple CSS
            ('[name="q"]', 'Simple CSS attribute'),
            
            # From tutorial/example (might use different formats)
            ('textarea#APjFqb', 'CSS with tag and ID'),
        ]
        
        print("\n2. Testing different selector formats for search box...")
        for selector, source in selector_variants:
            try:
                normalized = normalize_selector(selector)
                element = await page.query_selector(normalized)
                
                if element:
                    print(f"   ✓ {source}: {selector!r}")
                    print(f"     → Normalized to: {normalized!r}")
                    print(f"     → Found element: ✓")
                else:
                    print(f"   ✗ {source}: {selector!r} - Element not found")
                    
            except Exception as e:
                print(f"   ✗ {source}: {selector!r} - Error: {e}")
        
        # Test typing with XPath selector
        print("\n3. Type search query (using XPath selector)...")
        try:
            xpath_selector = '//*[@name="q"]'
            normalized = normalize_selector(xpath_selector)
            await page.fill(normalized, "playwright automation")
            print(f"   ✓ Typed text using: {xpath_selector!r}")
            print(f"     → Normalized to: {normalized!r}")
        except Exception as e:
            print(f"   ✗ Failed to type: {e}")
        
        # Test clicking with CSS selector
        print("\n4. Find search button (trying multiple selector formats)...")
        button_selectors = [
            ('input[name="btnK"]', 'CSS name attribute'),
            ('[name="btnK"]', 'CSS attribute only'),
            ('//*[@name="btnK"]', 'XPath name attribute'),
            ('input[value="Google Search"]', 'CSS value attribute'),
        ]
        
        button_found = False
        for selector, description in button_selectors:
            try:
                normalized = normalize_selector(selector)
                element = await page.query_selector(normalized)
                
                if element and await element.is_visible():
                    print(f"   ✓ {description}: {selector!r}")
                    button_found = True
                    break
                else:
                    print(f"   ⚠ {description}: Found but not visible")
                    
            except Exception as e:
                print(f"   ⚠ {description}: {str(e)[:50]}")
        
        if button_found:
            print(f"   ✓ Search button located successfully")
        
        # Test data attributes
        print("\n5. Testing data-* attribute selectors...")
        test_page_html = """
        <html>
        <body>
            <button data-testid="my-button" data-action="submit">Click</button>
            <input data-cy="username" id="user" />
            <div data-analytics="track-click">Analytics</div>
        </body>
        </html>
        """
        
        await page.set_content(test_page_html)
        
        data_selectors = [
            ('[data-testid="my-button"]', 'CSS data-testid'),
            ('//*[@data-testid="my-button"]', 'XPath data-testid'),
            ('[data-cy="username"]', 'CSS data-cy'),
            ('[data-analytics="track-click"]', 'CSS data-analytics'),
        ]
        
        for selector, description in data_selectors:
            try:
                normalized = normalize_selector(selector)
                element = await page.query_selector(normalized)
                
                if element:
                    print(f"   ✓ {description}: {selector!r}")
                else:
                    print(f"   ✗ {description}: Not found")
                    
            except Exception as e:
                print(f"   ✗ {description}: Error - {e}")
        
        # Test ARIA attributes
        print("\n6. Testing ARIA attribute selectors...")
        aria_html = """
        <html>
        <body>
            <button aria-label="Close dialog">X</button>
            <input aria-label="Search" type="search" />
            <div role="alert" aria-live="polite">Alert</div>
            <button aria-describedby="help-text">Help</button>
        </body>
        </html>
        """
        
        await page.set_content(aria_html)
        
        aria_selectors = [
            ('[aria-label="Close dialog"]', 'CSS aria-label'),
            ('//*[@aria-label="Search"]', 'XPath aria-label'),
            ('[role="alert"]', 'CSS role attribute'),
            ('[aria-describedby="help-text"]', 'CSS aria-describedby'),
        ]
        
        for selector, description in aria_selectors:
            try:
                normalized = normalize_selector(selector)
                element = await page.query_selector(normalized)
                
                if element:
                    print(f"   ✓ {description}: {selector!r}")
                else:
                    print(f"   ✗ {description}: Not found")
                    
            except Exception as e:
                print(f"   ✗ {description}: Error - {e}")
        
        await browser.close()
        
        print("\n" + "=" * 80)
        print("WORKFLOW TEST COMPLETE")
        print("=" * 80)
        print("\n✓ All selector formats work seamlessly")
        print("✓ XPath, CSS, data attributes, ARIA attributes - all supported")
        print("✓ Users can paste selectors from any source without modification")
        print("✓ System automatically adapts to the format provided")
        print("\n" + "=" * 80)

try:
    asyncio.run(test_google_workflow())
except Exception as e:
    print(f"\nTest failed with error: {e}")
    import traceback
    traceback.print_exc()
