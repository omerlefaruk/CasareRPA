"""
CAPTCHA solving nodes for reCAPTCHA v2 and other CAPTCHA types.

Uses 2Captcha API (or compatible services like Anti-Captcha) to solve
reCAPTCHA v2 challenges including image-based puzzles.

Setup:
    1. Get API key from https://2captcha.com/
    2. Set environment variable: CAPTCHA_API_KEY=your_api_key
    3. Or configure in Credential Manager with key "2captcha"

Usage in workflow:
    1. DetectCaptchaNode - Check if CAPTCHA challenge is visible
    2. SolveCaptchaNode - Solve the CAPTCHA and inject response token
    3. Continue with form submission
"""

import asyncio
import os

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_TIMEOUT,
)

# 2Captcha API configuration
CAPTCHA_API_BASE = "https://2captcha.com"
CAPTCHA_POLL_INTERVAL = 5  # seconds between status checks
CAPTCHA_MAX_WAIT_TIME = 120  # max seconds to wait for solution


# =============================================================================
# DetectCaptchaNode - Detect if CAPTCHA challenge is visible
# =============================================================================


@properties(
    PropertyDef(
        "captcha_type",
        PropertyType.CHOICE,
        default="recaptcha_v2",
        label="CAPTCHA Type",
        tooltip="Type of CAPTCHA to detect",
        choices=["recaptcha_v2", "recaptcha_v3", "hcaptcha", "image_captcha"],
    ),
    PropertyDef(
        "challenge_selector",
        PropertyType.STRING,
        default="iframe[title*='recaptcha challenge'], .rc-imageselect",
        label="Challenge Selector",
        tooltip="Selector for the CAPTCHA challenge iframe/container",
    ),
    BROWSER_TIMEOUT,
)
@node(category="browser")
class DetectCaptchaNode(BrowserBaseNode):
    """
    Detect if a CAPTCHA challenge is currently visible on the page.

    This node checks for:
    - reCAPTCHA v2 image challenge popup
    - reCAPTCHA checkbox (unchecked)
    - hCaptcha challenge
    - Generic image CAPTCHA forms

    Outputs:
    - captcha_detected: True if CAPTCHA challenge is visible
    - captcha_type: Type of CAPTCHA detected
    - sitekey: The sitekey if extractable (needed for solving)
    """

    def __init__(self, node_id: str, name: str = "Detect CAPTCHA", **kwargs):
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "DetectCaptchaNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_output_port("captcha_detected", DataType.BOOLEAN)
        self.add_output_port("captcha_type", DataType.STRING)
        self.add_output_port("sitekey", DataType.STRING)
        self.add_output_port("page_url", DataType.STRING)

    async def execute(self, context) -> ExecutionResult:
        """Execute CAPTCHA detection."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)
            captcha_type = self.get_parameter("captcha_type", "recaptcha_v2")
            challenge_selector = self.get_parameter(
                "challenge_selector", "iframe[title*='recaptcha challenge'], .rc-imageselect"
            )
            timeout = int(self.get_parameter("timeout", 5000))

            logger.info(f"Detecting {captcha_type} CAPTCHA...")

            captcha_detected = False
            sitekey = ""
            page_url = page.url

            # Check for reCAPTCHA v2
            if captcha_type in ["recaptcha_v2", "recaptcha_v3"]:
                # Check for challenge iframe (image puzzle popup)
                try:
                    challenge = await page.wait_for_selector(
                        challenge_selector, timeout=timeout, state="visible"
                    )
                    if challenge:
                        captcha_detected = True
                        logger.info("reCAPTCHA challenge (image puzzle) detected!")
                except Exception:
                    logger.debug("No reCAPTCHA challenge iframe found")

                # If no challenge popup, check for unchecked checkbox
                if not captcha_detected:
                    try:
                        # Check if reCAPTCHA checkbox exists but isn't checked
                        checkbox = await page.query_selector(
                            "iframe[title*='reCAPTCHA'], .g-recaptcha"
                        )
                        if checkbox:
                            captcha_detected = True
                            logger.info("reCAPTCHA checkbox detected")
                    except Exception:
                        pass

                # Extract sitekey
                try:
                    sitekey = await page.evaluate("""
                        () => {
                            // Try data-sitekey attribute
                            const recaptcha = document.querySelector('.g-recaptcha, [data-sitekey]');
                            if (recaptcha && recaptcha.dataset.sitekey) {
                                return recaptcha.dataset.sitekey;
                            }

                            // Try grecaptcha object
                            if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
                                // Enterprise reCAPTCHA - sitekey in page source
                                const scripts = document.querySelectorAll('script[src*="recaptcha"]');
                                for (const script of scripts) {
                                    const match = script.src.match(/render=([^&]+)/);
                                    if (match) return match[1];
                                }
                            }

                            // Try to find in iframe src
                            const iframe = document.querySelector('iframe[src*="recaptcha"]');
                            if (iframe) {
                                const match = iframe.src.match(/k=([^&]+)/);
                                if (match) return match[1];
                            }

                            return '';
                        }
                    """)
                except Exception as e:
                    logger.debug(f"Could not extract sitekey: {e}")

            # Check for hCaptcha
            elif captcha_type == "hcaptcha":
                try:
                    hcaptcha = await page.wait_for_selector(
                        "iframe[src*='hcaptcha'], .h-captcha", timeout=timeout, state="visible"
                    )
                    captcha_detected = hcaptcha is not None
                except Exception:
                    pass

            # Set outputs
            self.set_output_value("page", page)
            self.set_output_value("captcha_detected", captcha_detected)
            self.set_output_value("captcha_type", captcha_type if captcha_detected else "")
            self.set_output_value("sitekey", sitekey)
            self.set_output_value("page_url", page_url)

            self.status = NodeStatus.SUCCESS

            if captcha_detected:
                logger.info(f"CAPTCHA detected: type={captcha_type}, sitekey={sitekey[:20]}...")
            else:
                logger.info("No CAPTCHA detected")

            return {
                "success": True,
                "data": {
                    "captcha_detected": captcha_detected,
                    "captcha_type": captcha_type if captcha_detected else "",
                    "sitekey": sitekey,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"CAPTCHA detection failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


# =============================================================================
# SolveCaptchaNode - Solve CAPTCHA using 2Captcha API
# =============================================================================


@properties(
    PropertyDef(
        "api_key",
        PropertyType.STRING,
        default="",
        label="2Captcha API Key",
        tooltip="API key from 2captcha.com (or use CAPTCHA_API_KEY env var)",
    ),
    PropertyDef(
        "sitekey",
        PropertyType.STRING,
        default="",
        label="Site Key",
        tooltip="reCAPTCHA sitekey (extracted automatically if connected to DetectCaptchaNode)",
    ),
    PropertyDef(
        "page_url",
        PropertyType.STRING,
        default="",
        label="Page URL",
        tooltip="URL of the page with CAPTCHA (extracted automatically)",
    ),
    PropertyDef(
        "invisible",
        PropertyType.BOOLEAN,
        default=False,
        label="Invisible reCAPTCHA",
        tooltip="Check if this is an invisible reCAPTCHA (no checkbox)",
    ),
    PropertyDef(
        "enterprise",
        PropertyType.BOOLEAN,
        default=False,
        label="Enterprise reCAPTCHA",
        tooltip="Check if this is Google reCAPTCHA Enterprise",
    ),
    PropertyDef(
        "max_wait_time",
        PropertyType.INTEGER,
        default=120,
        label="Max Wait Time (seconds)",
        tooltip="Maximum time to wait for CAPTCHA solution",
    ),
    PropertyDef(
        "auto_inject",
        PropertyType.BOOLEAN,
        default=True,
        label="Auto-Inject Token",
        tooltip="Automatically inject the solution token into the page",
    ),
)
@node(category="browser")
class SolveCaptchaNode(BrowserBaseNode):
    """
    Solve reCAPTCHA v2 using 2Captcha API service.

    This node:
    1. Submits the CAPTCHA details to 2Captcha API
    2. Waits for human workers to solve the challenge
    3. Injects the solution token into the page
    4. Optionally triggers the callback function

    Cost: ~$2.99 per 1000 normal CAPTCHAs (2Captcha pricing)

    Requires:
    - 2Captcha API key (set via api_key parameter or CAPTCHA_API_KEY env var)
    - httpx library (pip install httpx)
    """

    def __init__(self, node_id: str, name: str = "Solve CAPTCHA", **kwargs):
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "SolveCaptchaNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_input_port("sitekey", DataType.STRING)
        self.add_input_port("page_url", DataType.STRING)
        self.add_output_port("solved", DataType.BOOLEAN)
        self.add_output_port("token", DataType.STRING)
        self.add_output_port("cost", DataType.FLOAT)

    async def execute(self, context) -> ExecutionResult:
        """Execute CAPTCHA solving."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get API key (parameter > env var > credential manager)
            api_key = self.get_parameter("api_key", "")
            if not api_key:
                api_key = os.getenv("CAPTCHA_API_KEY", "")
            if not api_key:
                # Try credential manager
                try:
                    from casare_rpa.utils.credential_manager import get_credential

                    api_key = get_credential("2captcha") or ""
                except Exception:
                    pass

            if not api_key:
                raise ValueError(
                    "No CAPTCHA API key found. Set CAPTCHA_API_KEY environment variable "
                    "or configure in Credential Manager with key '2captcha'"
                )

            # Get sitekey (from input port or parameter)
            sitekey = self.get_input_value("sitekey")
            if not sitekey:
                sitekey = self.get_parameter("sitekey", "")
            if not sitekey:
                # Try to extract from page
                sitekey = await self._extract_sitekey(page)

            if not sitekey:
                raise ValueError("No sitekey provided or found on page")

            # Get page URL
            page_url = self.get_input_value("page_url")
            if not page_url:
                page_url = self.get_parameter("page_url", "")
            if not page_url:
                page_url = page.url

            invisible = self.get_parameter("invisible", False)
            enterprise = self.get_parameter("enterprise", False)
            max_wait_time = int(self.get_parameter("max_wait_time", 120))
            auto_inject = self.get_parameter("auto_inject", True)

            logger.info(f"Solving reCAPTCHA for {page_url[:50]}... (sitekey: {sitekey[:20]}...)")

            # Submit to 2Captcha
            token, cost = await self._solve_recaptcha_v2(
                api_key=api_key,
                sitekey=sitekey,
                page_url=page_url,
                invisible=invisible,
                enterprise=enterprise,
                max_wait_time=max_wait_time,
            )

            if not token:
                raise RuntimeError("Failed to get CAPTCHA solution from 2Captcha")

            logger.info(f"CAPTCHA solved! Token: {token[:30]}...")

            # Auto-inject token into page
            if auto_inject:
                await self._inject_token(page, token)
                logger.info("Token injected into page")

            # Set outputs
            self.set_output_value("page", page)
            self.set_output_value("solved", True)
            self.set_output_value("token", token)
            self.set_output_value("cost", cost)

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "solved": True,
                    "token_preview": token[:50] + "...",
                    "cost": cost,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"CAPTCHA solving failed: {e}")
            self.set_output_value("solved", False)
            return {"success": False, "error": str(e), "next_nodes": []}

    async def _extract_sitekey(self, page) -> str:
        """Extract reCAPTCHA sitekey from page."""
        try:
            return await page.evaluate("""
                () => {
                    // Try data-sitekey attribute
                    const recaptcha = document.querySelector('.g-recaptcha, [data-sitekey]');
                    if (recaptcha && recaptcha.dataset.sitekey) {
                        return recaptcha.dataset.sitekey;
                    }

                    // Try to find in iframe src
                    const iframe = document.querySelector('iframe[src*="recaptcha"]');
                    if (iframe) {
                        const match = iframe.src.match(/k=([^&]+)/);
                        if (match) return match[1];
                    }

                    return '';
                }
            """)
        except Exception:
            return ""

    async def _solve_recaptcha_v2(
        self,
        api_key: str,
        sitekey: str,
        page_url: str,
        invisible: bool = False,
        enterprise: bool = False,
        max_wait_time: int = 120,
    ) -> tuple[str, float]:
        """
        Submit reCAPTCHA to 2Captcha and wait for solution.

        Returns:
            Tuple of (token, cost) where cost is in USD
        """
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx required for CAPTCHA solving. Install with: pip install httpx") from None

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Submit CAPTCHA
            submit_params = {
                "key": api_key,
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": page_url,
                "json": 1,
            }

            if invisible:
                submit_params["invisible"] = 1
            if enterprise:
                submit_params["enterprise"] = 1

            logger.debug(f"Submitting to 2Captcha: sitekey={sitekey[:20]}, url={page_url}")

            submit_response = await client.post(
                f"{CAPTCHA_API_BASE}/in.php",
                data=submit_params,
            )
            submit_data = submit_response.json()

            if submit_data.get("status") != 1:
                error = submit_data.get("request", "Unknown error")
                raise RuntimeError(f"2Captcha submission failed: {error}")

            request_id = submit_data["request"]
            logger.info(f"CAPTCHA submitted to 2Captcha. Request ID: {request_id}")

            # Step 2: Poll for result
            start_time = asyncio.get_event_loop().time()

            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_wait_time:
                    raise TimeoutError(f"CAPTCHA solving timed out after {max_wait_time} seconds")

                await asyncio.sleep(CAPTCHA_POLL_INTERVAL)

                result_response = await client.get(
                    f"{CAPTCHA_API_BASE}/res.php",
                    params={
                        "key": api_key,
                        "action": "get",
                        "id": request_id,
                        "json": 1,
                    },
                )
                result_data = result_response.json()

                if result_data.get("status") == 1:
                    token = result_data["request"]
                    # Typical cost is ~$0.003 per CAPTCHA
                    cost = 0.003
                    return token, cost

                request_status = result_data.get("request", "")
                if request_status == "CAPCHA_NOT_READY":
                    logger.debug(f"CAPTCHA still processing... ({int(elapsed)}s elapsed)")
                    continue

                # Error occurred
                raise RuntimeError(f"2Captcha error: {request_status}")

    async def _inject_token(self, page, token: str) -> None:
        """Inject the reCAPTCHA token into the page."""
        await page.evaluate(
            """
            (token) => {
                // Set the response textarea
                const textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {
                    textarea.style.display = 'block';
                    textarea.value = token;
                    textarea.style.display = 'none';
                }

                // Also try hidden inputs
                const hiddenInputs = document.querySelectorAll('input[name="g-recaptcha-response"]');
                hiddenInputs.forEach(input => {
                    input.value = token;
                });

                // Try to trigger callback if available
                if (typeof grecaptcha !== 'undefined' && grecaptcha.getResponse) {
                    // Find the widget ID and execute callback
                    try {
                        const widgetId = grecaptcha.enterprise ?
                            Object.keys(___grecaptcha_cfg.clients || {})[0] :
                            document.querySelector('.g-recaptcha')?.dataset?.widgetId || 0;

                        const callback = grecaptcha.enterprise ?
                            ___grecaptcha_cfg.clients[widgetId]?.callback :
                            window.___grecaptcha_cfg?.clients?.[widgetId]?.callback?.callback;

                        if (callback && typeof callback === 'function') {
                            callback(token);
                        }
                    } catch (e) {
                        console.log('Could not trigger callback:', e);
                    }
                }
            }
        """,
            token,
        )


# =============================================================================
# Export nodes
# =============================================================================

__all__ = [
    "DetectCaptchaNode",
    "SolveCaptchaNode",
]
