"""
AI-powered CAPTCHA solving using vision models.

Solves image-based CAPTCHA challenges (like reCAPTCHA "Select all images with X")
using Google Gemini via Google OAuth or GLM (Z.ai) via API key.

Supported models:
- GLM-4.7 (Recommended - Z.ai Coding Plan)
- GLM-4.6, GLM-4.5 (Z.ai)
- gemini-3-flash-preview
- gemini-2.0-flash-exp
- gemini-1.5-flash

Much faster than human CAPTCHA solving services (~2-5 seconds vs 15-60 seconds).
"""

import asyncio
import base64
import re
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import BROWSER_TIMEOUT

# Google Generative AI API endpoint
GOOGLE_GENAI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _get_vision_credentials(config: Any | None = None) -> list[tuple[str, str]]:
    """Get list of credentials that support vision models for dropdown."""
    try:
        from casare_rpa.infrastructure.security.credential_store import get_credential_store

        store = get_credential_store()
        results = []

        # Get Google OAuth credentials
        google_creds = store.get_credentials_for_dropdown(category="google")
        results.extend(google_creds)

        # Get GLM API key credentials
        llm_creds = store.list_credentials(category="llm")
        for cred in llm_creds:
            cred_data = store.get_credential(cred["id"])
            if cred_data and cred_data.get("provider") == "glm":
                results.append((cred["id"], f"{cred['name']} (GLM)"))

        return results
    except Exception:
        return []


def _get_default_credential(config: Any | None = None) -> str:
    """Get the default credential (GLM first, then Google OAuth)."""
    try:
        from casare_rpa.infrastructure.security.credential_store import get_credential_store

        store = get_credential_store()

        # Try GLM credentials first (preferred for captcha solving)
        llm_creds = store.list_credentials(category="llm")
        for cred in llm_creds:
            cred_data = store.get_credential(cred["id"])
            if cred_data and cred_data.get("provider") == "glm":
                return cred["id"]

        # Fallback to Google OAuth
        google_creds = store.list_google_credentials()
        if google_creds:
            return google_creds[0]["id"]

    except Exception:
        pass
    return ""


# =============================================================================
# SolveCaptchaAINode - Solve CAPTCHA using AI Vision
# =============================================================================


@properties(
    PropertyDef(
        "credential_id",
        PropertyType.CHOICE,
        default="",
        dynamic_default=_get_default_credential,
        dynamic_choices=_get_vision_credentials,
        label="Credential",
        tooltip="Select a stored credential (GLM API Key or Google OAuth)",
        default_selection=True,
    ),
    PropertyDef(
        "api_key",
        PropertyType.STRING,
        default="",
        label="Or API Key",
        tooltip="Manual API key override (GLM or Google API key)",
    ),
    PropertyDef(
        "model",
        PropertyType.CHOICE,
        default="glm-4.7",
        label="Vision Model",
        tooltip="AI model to use for image analysis",
        status="live",
        choices=[
            # GLM Models (Z.ai) - Recommended
            "glm-4.7",
            "glm-4.6",
            "glm-4.5",
            # Google Gemini Models
            "models/gemini-3-flash-preview",
            "models/gemini-2.0-flash-exp",
            "models/gemini-1.5-flash",
        ],
    ),
    PropertyDef(
        "max_attempts",
        PropertyType.INTEGER,
        default=10,
        label="Max Attempts",
        tooltip="Maximum number of solving attempts before giving up (suggested 5-10 for reCAPTCHA)",
    ),
    BROWSER_TIMEOUT,
)
@node(category="browser")
class SolveCaptchaAINode(BrowserBaseNode):
    """
    Solve reCAPTCHA image challenges using AI vision models.

    This node:
    1. Takes a screenshot of the CAPTCHA challenge
    2. Sends it to GLM (Z.ai) or Google Gemini
    3. AI identifies which images match the target (e.g., "bridges")
    4. Clicks the identified images and submits

    Much faster than human CAPTCHA solving services (~2-5 seconds).

    Requires:
    - Stored GLM API Key credential (recommended) OR
    - Stored Google OAuth credential OR
    - Manual API key
    """


    def __init__(self, node_id: str, name: str = "Solve CAPTCHA (AI)", **kwargs):
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "SolveCaptchaAINode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_output_port("solved", DataType.BOOLEAN)
        self.add_output_port("attempts", DataType.INTEGER)

    async def execute(self, context) -> ExecutionResult:
        """Execute AI-powered CAPTCHA solving."""
        self.status = NodeStatus.RUNNING

        try:
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMConfig,
                LLMProvider,
                LLMResourceManager,
            )

            page = self.get_page(context)

            # Get params
            credential_id = self.get_parameter("credential_id", "")
            api_key = self.get_parameter("api_key", "")

            # Use user-specified model or default to glm-4.7
            requested_model = self.get_parameter("model", "")
            if not requested_model:
                requested_model = "glm-4.7"

            # Normalize model name (remove models/ prefix if present)
            if requested_model.startswith("models/"):
                requested_model = requested_model.replace("models/", "")

            # Determine if using GLM or Google based on model and credential
            is_glm_model = requested_model.startswith("glm-")

            # Track authentication info
            oauth_access_token = None
            glm_api_key = None

            if credential_id:
                try:
                    from casare_rpa.infrastructure.security.credential_store import (
                        get_credential_store,
                    )

                    store = get_credential_store()
                    info = store.get_credential_info(credential_id)
                    if info:
                        cred_type = info.get("type", "")
                        cred_category = info.get("category", "")
                        logger.info(f"Using credential type: {cred_type}, category: {cred_category}")

                        # For Google OAuth, get access token for direct API calls
                        if cred_type == "google_oauth":
                            from casare_rpa.infrastructure.security.google_oauth import (
                                get_google_oauth_manager,
                            )

                            oauth_manager = await get_google_oauth_manager()
                            oauth_access_token = await oauth_manager.get_access_token(credential_id)
                            logger.info("Got OAuth access token for direct Google AI API calls")

                        # For LLM API key credentials, check if it's GLM
                        elif cred_type == "api_key" and cred_category == "llm":
                            cred_data = store.get_credential(credential_id)
                            if cred_data and cred_data.get("provider") == "glm":
                                glm_api_key = cred_data.get("api_key")
                                logger.info("Got GLM API key from credential store")
                            else:
                                # Non-GLM API key - might be a Google API key
                                api_key = cred_data.get("api_key", "") if cred_data else ""
                        else:
                            logger.warning(
                                f"Unexpected credential type: {cred_type}, proceeding anyway"
                            )
                except Exception as e:
                    logger.warning(f"Could not get credential: {e}")

            # Manual API key override
            if api_key and not glm_api_key and not oauth_access_token:
                if is_glm_model:
                    glm_api_key = api_key
                # else: api_key is used for Google

            logger.info(
                f"Solving CAPTCHA with model: {requested_model} "
                f"(Credential: {credential_id if credential_id else 'None/Auto'}, "
                f"GLM: {'Yes' if glm_api_key else 'No'}, "
                f"OAuth: {'Yes' if oauth_access_token else 'No'})"
            )

            # Configure LLM Resource Manager for fallback
            llm_client = LLMResourceManager()

            # Determine provider for config
            if is_glm_model:
                provider = LLMProvider.GLM
            else:
                provider = LLMProvider.CUSTOM

            llm_config = LLMConfig(
                provider=provider,
                model=requested_model,
                api_key=glm_api_key or api_key if (glm_api_key or api_key) else None,
                credential_id=credential_id if credential_id else None,
            )
            llm_client.configure(llm_config)

            model = requested_model
            max_attempts = int(self.get_parameter("max_attempts", 10))
            timeout = int(self.get_parameter("timeout", 45000))

            solved = False
            attempts = 0
            clicked_tiles = set()  # Track clicked tiles to avoid re-clicking (unselecting)


            for attempt in range(max_attempts):
                attempts = attempt + 1
                logger.info(f"CAPTCHA solving attempt {attempts}/{max_attempts}")

                try:
                    # Check if CAPTCHA challenge is visible
                    challenge_frame = await self._find_captcha_frame(page, timeout)

                    if not challenge_frame:
                        logger.info("No CAPTCHA challenge found - may already be solved")
                        solved = True
                        break

                    # Get the challenge details (target object and images)
                    target, grid_coords, grid_size = await self._analyze_challenge(
                        challenge_frame, llm_client, model, oauth_access_token, glm_api_key
                    )

                    if not grid_coords:
                        logger.warning("AI couldn't identify any matching images")
                        # Click verify anyway in case it's already solved
                        await self._click_verify(challenge_frame)
                        await self._wait_for_stability(challenge_frame, timeout_ms=3000)
                        clicked_tiles.clear()  # Reset after verify
                        continue

                    # Filter out already clicked tiles to prevent unselecting
                    new_coords = [c for c in grid_coords if c not in clicked_tiles]

                    if not new_coords:
                        logger.info(
                            "No new tiles to click - all already selected. Clicking verify..."
                        )
                        await self._click_verify(challenge_frame)
                        await self._wait_for_stability(challenge_frame, timeout_ms=3000)

                        still_visible = await self._is_challenge_visible(page)
                        if not still_visible:
                            solved = True
                            logger.info("CAPTCHA solved successfully!")
                            break
                        else:
                            # Reset tracking if verify failed - might need to start fresh
                            clicked_tiles.clear()
                            continue

                    logger.info(
                        f"AI identified {len(grid_coords)} tiles, clicking {len(new_coords)} NEW tiles"
                    )

                    # Click only the NEW identified images
                    await self._click_images(challenge_frame, new_coords, grid_size)

                    # Track clicked tiles
                    clicked_tiles.update(new_coords)

                    # Wait for stability (no fading tiles)
                    logger.debug("Waiting for image grid stability...")
                    await self._wait_for_stability(challenge_frame)

                    # DYNAMIC GRID HANDLING (3x3)
                    if grid_size == (3, 3):
                        logger.info(
                            f"Dynamic grid (3x3): Total clicked so far: {len(clicked_tiles)}"
                        )
                        await self._wait_for_stability(challenge_frame, timeout_ms=5000)
                        continue

                    # STATIC GRID HANDLING (4x4)
                    logger.info("Static grid (4x4): Clicking verify...")
                    await self._click_verify(challenge_frame)

                    await self._wait_for_stability(challenge_frame, timeout_ms=3000)

                    still_visible = await self._is_challenge_visible(page)
                    if not still_visible:
                        solved = True
                        logger.info("CAPTCHA solved successfully!")
                        break
                    else:
                        logger.info("CAPTCHA not yet solved, retrying...")
                        clicked_tiles.clear()

                except Exception as e:
                    logger.warning(f"Attempt {attempts} failed: {e}")
                    clicked_tiles.clear()
                    if attempt < max_attempts - 1:
                        await self._wait_for_stability(
                            challenge_frame, timeout_ms=2000
                        ) if challenge_frame else None

            # Set outputs
            self.set_output_value("page", page)
            self.set_output_value("solved", solved)
            self.set_output_value("attempts", attempts)

            if solved:
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.SUCCESS  # Not error, just logical failure

            return {
                "success": True,
                "data": {"solved": solved, "attempts": attempts},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"CAPTCHA solver crashed: {e}")
            self.set_output_value("solved", False)
            return {"success": False, "error": str(e), "next_nodes": []}

    async def _find_captcha_frame(self, page, timeout: int):
        """Find the reCAPTCHA challenge iframe."""
        try:
            # Look for the challenge iframe (the popup with images)
            selectors = [
                'iframe[title*="recaptcha challenge"]',
                'iframe[src*="bframe"]',
                'iframe[src*="recaptcha"][src*="k="]',
            ]

            for selector in selectors:
                try:
                    iframe = await page.wait_for_selector(
                        selector, timeout=min(timeout, 3000), state="visible"
                    )
                    if iframe:
                        frame = await iframe.content_frame()
                        if frame:
                            # Check if this frame has the image grid
                            grid = await frame.query_selector(
                                ".rc-imageselect-table, .rc-image-tile-wrapper"
                            )
                            if grid:
                                return frame
                except Exception:
                    continue

            return None
        except Exception as e:
            logger.debug(f"Could not find CAPTCHA frame: {e}")
            return None

    async def _analyze_challenge(
        self,
        frame,
        llm_client,
        model: str,
        access_token: str | None = None,
        glm_api_key: str | None = None,
    ) -> tuple[str, list[tuple[int, int]], tuple[int, int]]:
        """
        Analyze the CAPTCHA challenge using AI vision.

        Uses one of:
        - GLM API if glm_api_key is provided (recommended)
        - Direct Google AI API if access_token is provided
        - LiteLLM as fallback
        """
        # Take screenshot
        frame_handle = await frame.frame_element()
        screenshot_bytes = await frame_handle.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        # Get instruction
        instruction = ""
        try:
            instruction_elem = await frame.query_selector(
                ".rc-imageselect-desc-wrapper, .rc-imageselect-desc, .rc-imageselect-instructions"
            )
            if instruction_elem:
                instruction = await instruction_elem.inner_text()
        except Exception:
            pass

        # Determine grid size
        grid_size = await self._get_grid_size(frame)

        # Build prompt
        prompt = self._build_analysis_prompt(instruction, grid_size)

        # Use GLM API if we have a GLM API key (preferred)
        if glm_api_key:
            ai_response = await self._call_glm_vision(
                prompt=prompt, image_b64=screenshot_b64, model=model, api_key=glm_api_key
            )
        # Use direct Google AI API if we have an OAuth access token
        elif access_token:
            ai_response = await self._call_google_ai_direct(
                prompt=prompt, image_b64=screenshot_b64, model=model, access_token=access_token
            )
        else:
            # Fallback to LiteLLM
            from casare_rpa.infrastructure.resources.llm_resource_manager import ImageContent

            response = await llm_client.vision_completion(
                prompt=prompt,
                images=[ImageContent(base64_data=screenshot_b64, media_type="image/png")],
                model=model,
                temperature=0.1,
                max_tokens=500,
            )
            ai_response = response.content

        logger.debug(f"AI response: {ai_response}")

        # Parse the AI response
        target, coords = self._parse_ai_response(ai_response, instruction, grid_size)

        return target, coords, grid_size

    async def _call_glm_vision(
        self, prompt: str, image_b64: str, model: str, api_key: str
    ) -> str:
        """
        Call GLM (Z.ai) vision API to analyze CAPTCHA image.

        Uses GLMClient.analyze_image for vision tasks.
        """
        from casare_rpa.infrastructure.ai import GLMClient

        # Create GLM client with the provided API key
        client = GLMClient(api_key=api_key, model=model)

        logger.debug(f"Calling GLM Vision API with model: {model}")

        try:
            # Use GLM's analyze_image method for vision tasks
            response = await client.analyze_image(
                prompt=prompt,
                image_base64=image_b64,
                model=model,
            )

            return response.content

        except Exception as e:
            logger.error(f"GLM Vision API error: {e}")
            raise Exception(f"GLM Vision API error: {e}") from e

    async def _call_google_ai_direct(
        self, prompt: str, image_b64: str, model: str, access_token: str
    ) -> str:
        """
        Call Google Generative AI API directly using OAuth access token.

        This bypasses LiteLLM to use the OAuth token directly with Google's API.
        """
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        # Clean up model name
        clean_model = model
        for prefix in ["gemini/", "models/", "vertex_ai/"]:
            if clean_model.startswith(prefix):
                clean_model = clean_model[len(prefix) :]

        url = GOOGLE_GENAI_API_URL.format(model=clean_model)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Build request body with image
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": image_b64}},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
            },
        }

        logger.debug(f"Calling Google AI API: {url}")

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=False,  # Google API is trusted
            max_retries=2,
            default_timeout=60.0,
        )

        async with UnifiedHttpClient(config) as http_client:
            response = await http_client.post(url, json=payload, headers=headers)

            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Google AI API error ({response.status}): {error_text}")
                raise Exception(f"Google AI API error: {response.status} - {error_text}")

            result = await response.json()

            # Extract the text response
            try:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return content
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse Google AI response: {result}")
                raise Exception(f"Failed to parse Google AI response: {e}") from e

    async def _get_grid_size(self, frame) -> tuple[int, int]:
        """Determine the CAPTCHA grid size (3x3 or 4x4)."""
        try:
            # Count tiles
            tiles = await frame.query_selector_all(".rc-image-tile-wrapper, .rc-imageselect-tile")
            count = len(tiles)

            if count == 16:
                return (4, 4)
            elif count == 9:
                return (3, 3)
            else:
                # Try to detect from table structure
                table = await frame.query_selector(".rc-imageselect-table-33")
                if table:
                    return (3, 3)
                table = await frame.query_selector(".rc-imageselect-table-44")
                if table:
                    return (4, 4)

            return (3, 3)  # Default to 3x3
        except Exception:
            return (3, 3)

    def _build_analysis_prompt(self, instruction: str, grid_size: tuple[int, int]) -> str:
        """Build the prompt for AI analysis."""
        rows, cols = grid_size

        # Extract the target object from instruction
        target = "the requested objects"
        if instruction:
            # Try to extract what we're looking for
            match = re.search(
                r"(?:select|click|verify).*?(?:all\s+)?(?:images?\s+)?(?:with|containing|of|showing)\s+(.+?)(?:\.|$)",
                instruction.lower(),
            )
            if match:
                target = match.group(1).strip()

        prompt = f"""You are analyzing a reCAPTCHA image challenge. The challenge shows a {rows}x{cols} grid of images.

INSTRUCTION FROM CAPTCHA: "{instruction}"

The grid is numbered as follows (row, column):
"""
        # Build grid reference
        for r in range(1, rows + 1):
            row_items = [f"({r},{c})" for c in range(1, cols + 1)]
            prompt += "  " + " ".join(row_items) + "\n"

        prompt += f"""
Your task: Identify which grid cells contain images of "{target}".

IMPORTANT RULES:
1. Look carefully at each image in the grid
2. Identify ALL images that match "{target}"
3. Response format: List the coordinates like this: (1,2), (2,3), (3,1)
4. If NO images match, respond with: NONE
5. Be confident but not over-inclusive - only select clear matches

RESPOND WITH ONLY THE COORDINATES, nothing else."""

        return prompt

    def _parse_ai_response(
        self, response: str, instruction: str, grid_size: tuple[int, int]
    ) -> tuple[str, list[tuple[int, int]]]:
        """Parse AI response to extract grid coordinates."""
        target = "requested object"
        if instruction:
            match = re.search(r"with\s+(.+?)(?:\.|$)", instruction.lower())
            if match:
                target = match.group(1).strip()

        coords = []

        if "none" in response.lower():
            return target, []

        # Find all coordinate patterns like (1,2) or (1, 2) or 1,2
        pattern = r"\(?\s*(\d+)\s*,\s*(\d+)\s*\)?"
        matches = re.findall(pattern, response)

        rows, cols = grid_size
        for match in matches:
            row, col = int(match[0]), int(match[1])
            if 1 <= row <= rows and 1 <= col <= cols:
                coords.append((row, col))

        # Remove duplicates while preserving order
        seen = set()
        unique_coords = []
        for coord in coords:
            if coord not in seen:
                seen.add(coord)
                unique_coords.append(coord)

        return target, unique_coords

    async def _click_images(
        self, frame, coords: list[tuple[int, int]], grid_size: tuple[int, int]
    ) -> None:
        """Click the images at the specified grid coordinates."""
        rows, cols = grid_size
        for row, col in coords:
            try:
                # Calculate index based on grid width
                index = (row - 1) * cols + (col - 1)

                # Try different selectors
                selectors = [
                    f".rc-imageselect-tile:nth-child({index + 1})",
                    f".rc-image-tile-wrapper:nth-child({index + 1})",
                    f"table.rc-imageselect-table td:nth-child({col}) img",
                ]

                # Try clicking by table row/col
                cell_selector = (
                    f"table.rc-imageselect-table-33 tr:nth-child({row}) td:nth-child({col})"
                )
                cell = await frame.query_selector(cell_selector)
                if cell:
                    await cell.click()
                    logger.debug(f"Clicked cell ({row}, {col})")
                    await self._wait_for_stability(frame, selector=cell_selector)
                    continue

                # Try 4x4 grid
                cell_selector = (
                    f"table.rc-imageselect-table-44 tr:nth-child({row}) td:nth-child({col})"
                )
                cell = await frame.query_selector(cell_selector)
                if cell:
                    await cell.click()
                    logger.debug(f"Clicked cell ({row}, {col})")
                    await self._wait_for_stability(frame, selector=cell_selector)
                    continue

                # Fallback: click by index
                tiles = await frame.query_selector_all(
                    ".rc-imageselect-tile, .rc-image-tile-wrapper"
                )
                if index < len(tiles):
                    tile = tiles[index]
                    await tile.click()
                    logger.debug(f"Clicked tile index {index}")

                    # DYNAMIC HANDLING: Wait for this specific tile to stabilize
                    await self._wait_for_stability(frame, selector=selectors[0])
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.warning(f"Failed to click ({row}, {col}): {e}")

    async def _wait_for_stability(
        self, frame, selector: str = None, timeout_ms: int = 5000
    ) -> None:
        """Wait for the CAPTCHA grid to stop animating/fading."""
        try:
            # If a specific selector is provided, check only that, otherwise check whole grid
            fading_selectors = [
                ".rc-image-tile-fading-out",
                ".rc-image-tile-fading-in",
                ".rc-image-tile-loading",
            ]

            if selector:
                # Add fading classes to the specific selector
                # Playwright specific: we need to ensure the selector is correct for the join
                # If selector is a CSS selector, we can append the class
                grid_selector = ", ".join([f"{selector}{cls}" for cls in fading_selectors])
            else:
                # Check for any fading tile in the whole frame
                grid_selector = ", ".join(fading_selectors)

            # Wait for fading to stop
            start_time = asyncio.get_event_loop().time()
            stable_count = 0

            while (asyncio.get_event_loop().time() - start_time) < (timeout_ms / 1000.0):
                is_fading = await frame.query_selector(grid_selector)
                if not is_fading:
                    stable_count += 1
                    if stable_count >= 2:  # Must be stable for two consecutive checks
                        break
                else:
                    stable_count = 0
                await asyncio.sleep(0.3)

            if stable_count < 2:
                logger.debug("Stability wait timed out - proceeding anyway")

        except Exception as e:
            logger.debug(f"Error in stability wait: {e}")

    async def _click_verify(self, frame) -> None:
        """Click the verify/submit button."""
        try:
            verify_selectors = [
                "#recaptcha-verify-button",
                ".rc-button-default",
                'button[id*="verify"]',
                ".verify-button-holder button",
            ]

            for selector in verify_selectors:
                button = await frame.query_selector(selector)
                if button:
                    await button.click()
                    logger.debug("Clicked verify button")
                    return

        except Exception as e:
            logger.warning(f"Failed to click verify: {e}")

    async def _is_challenge_visible(self, page) -> bool:
        """Check if the CAPTCHA challenge is still visible."""
        try:
            # Try to find the challenge iframe
            selectors = [
                'iframe[title*="recaptcha challenge"]',
                'iframe[src*="bframe"]',
            ]

            for selector in selectors:
                iframe = await page.query_selector(selector)
                if iframe:
                    is_visible = await iframe.is_visible()
                    if is_visible:
                        return True

            return False
        except Exception:
            return False


# =============================================================================
# Export
# =============================================================================

__all__ = ["SolveCaptchaAINode"]
