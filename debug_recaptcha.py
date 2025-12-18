import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_recaptcha():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()

        logger.info("Navigating to Login Page...")
        page.goto("https://websube.ckbogazici.com.tr/Giris/Giris")
        page.wait_for_load_state("networkidle")

        logger.info("Listing Frames:")
        for frame in page.frames:
            logger.info(f"Frame: name='{frame.name}', url='{frame.url}'")

        logger.info("Attempting to find reCAPTCHA frame...")
        # Try finding by title first (common)
        recaptcha_frame = None
        for frame in page.frames:
            if "google.com/recaptcha" in frame.url:
                logger.info(f"Found reCAPTCHA frame candidate: {frame.url}")
                recaptcha_frame = frame
                break

        if recaptcha_frame:
            logger.info("Locating checkbox inside frame...")
            try:
                # Try standard selector
                checkbox = recaptcha_frame.locator(".recaptcha-checkbox-border")
                if checkbox.count() > 0:
                    logger.info("Found .recaptcha-checkbox-border")
                    checkbox.click(force=True)
                    logger.info("Clicked checkbox")
                    page.screenshot(path="debug_click_success.png")
                else:
                    logger.warning("Could not find .recaptcha-checkbox-border")
                    logger.info("Dumping frame HTML:")
                    # logger.info(recaptcha_frame.content()) # Too verbose, maybe just specific elements

                    # Try alternative selector
                    checkbox_alt = recaptcha_frame.locator("#recaptcha-anchor")
                    if checkbox_alt.count() > 0:
                        logger.info("Found #recaptcha-anchor")
                        checkbox_alt.click()
            except Exception as e:
                logger.error(f"Error clicking: {e}")
        else:
            logger.error("No frame with 'google.com/recaptcha' found.")

        input("Press Enter to close browser...")
        browser.close()


if __name__ == "__main__":
    debug_recaptcha()
