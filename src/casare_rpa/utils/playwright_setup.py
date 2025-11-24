"""
Playwright Browser Auto-Setup
Automatically installs Playwright browsers on first run.
"""
import subprocess
import sys
from pathlib import Path
from loguru import logger

def check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    # Check for chromium browser directory
    if sys.platform == "win32":
        browser_path = Path.home() / "AppData" / "Local" / "ms-playwright"
    else:
        browser_path = Path.home() / ".cache" / "ms-playwright"
    
    return browser_path.exists() and any(browser_path.iterdir())

def install_playwright_browsers() -> bool:
    """Install Playwright browsers (chromium only for now)."""
    logger.info("📥 Installing Playwright browsers (this may take a few minutes)...")
    logger.info("⏳ Please wait, downloading Chromium browser...")
    
    try:
        # Run playwright install
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        logger.info("✅ Playwright browsers installed successfully!")
        logger.debug(f"Installation output: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install Playwright browsers: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Browser installation timed out. Please check your internet connection.")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during browser installation: {e}")
        return False

def ensure_playwright_ready() -> bool:
    """
    Ensure Playwright browsers are installed, install if missing.
    
    Returns:
        True if browsers are ready, False if installation failed
    """
    if not check_playwright_browsers():
        logger.warning("⚠️  Playwright browsers not found. Installing...")
        return install_playwright_browsers()
    else:
        logger.info("✅ Playwright browsers already installed")
        return True
