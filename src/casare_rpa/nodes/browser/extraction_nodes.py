"""
Browser extraction and download nodes.

Handles extracting data (images) and downloading files.
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "min_width",
        PropertyType.INTEGER,
        default=0,
        label="Min Width (px)",
        tooltip="Minimum image width in pixels (0 = no filter)",
        min_value=0,
    ),
    PropertyDef(
        "min_height",
        PropertyType.INTEGER,
        default=0,
        label="Min Height (px)",
        tooltip="Minimum image height in pixels (0 = no filter)",
        min_value=0,
    ),
    PropertyDef(
        "include_backgrounds",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Backgrounds",
        tooltip="Include CSS background images",
    ),
    PropertyDef(
        "file_types",
        PropertyType.STRING,
        default="",
        label="File Types",
        tooltip="Comma-separated file extensions to include (empty = all)",
        placeholder="jpg,png,webp",
    ),
)
@node(category="browser")
class GetAllImagesNode(BaseNode):
    """
    Get all images from the current page.

    Extracts all image URLs (from <img> tags and CSS background images)
    from the current page. Can filter by minimum size and file type.

    Outputs:
        - images: List of image URLs
        - count: Number of images found
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: none -> images, count

    def __init__(self, node_id: str, name: str = "Get All Images", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetAllImagesNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_output_port("images", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Extract all image URLs from the page."""
        try:
            page = context.get_active_page()
            if not page:
                raise ValueError("No active page. Launch browser and navigate first.")

            min_width = self.get_parameter("min_width", 0)
            min_height = self.get_parameter("min_height", 0)
            include_backgrounds = self.get_parameter("include_backgrounds", True)
            file_types_str = self.get_parameter("file_types", "")

            # Parse allowed file types
            allowed_types = []
            if file_types_str:
                allowed_types = [
                    f".{t.strip().lower().lstrip('.')}" for t in file_types_str.split(",")
                ]

            # JavaScript to extract all images
            js_code = """
            (includeBackgrounds) => {
                const images = [];
                const seen = new Set();

                // Get all <img> elements
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src || img.getAttribute('data-lazy-src');
                    if (src && !seen.has(src)) {
                        seen.add(src);
                        images.push({
                            url: src,
                            width: img.naturalWidth || img.width || 0,
                            height: img.naturalHeight || img.height || 0,
                            alt: img.alt || '',
                            type: 'img'
                        });
                    }
                });

                // Get <source> elements in <picture>
                document.querySelectorAll('picture source').forEach(source => {
                    const srcset = source.srcset;
                    if (srcset) {
                        // Parse srcset and get the largest image
                        const urls = srcset.split(',').map(s => s.trim().split(' ')[0]);
                        urls.forEach(url => {
                            if (url && !seen.has(url)) {
                                seen.add(url);
                                images.push({
                                    url: url,
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'source'
                                });
                            }
                        });
                    }
                });

                // Get CSS background images if requested
                if (includeBackgrounds) {
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const match = bgImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                            if (match && match[1] && !seen.has(match[1])) {
                                seen.add(match[1]);
                                images.push({
                                    url: match[1],
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'background'
                                });
                            }
                        }
                    });
                }

                return images;
            }
            """

            # Execute JavaScript
            all_images = await page.evaluate(js_code, include_backgrounds)

            # Filter by size and file type
            filtered_images = []
            for img in all_images:
                url = img.get("url", "")
                if not url or url.startswith("data:"):
                    continue

                # Check size filter
                width = img.get("width", 0)
                height = img.get("height", 0)
                if min_width > 0 and width < min_width:
                    continue
                if min_height > 0 and height < min_height:
                    continue

                # Check file type filter
                if allowed_types:
                    url_lower = url.lower().split("?")[0]  # Remove query params
                    if not any(url_lower.endswith(ext) for ext in allowed_types):
                        continue

                filtered_images.append(url)

            # Set outputs
            self.set_output_value("images", filtered_images)
            self.set_output_value("count", len(filtered_images))

            self.status = NodeStatus.SUCCESS
            logger.info(f"Found {len(filtered_images)} images on page")

            return {
                "success": True,
                "data": {"images": filtered_images, "count": len(filtered_images)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get images: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "url",
        PropertyType.STRING,
        required=True,
        label="URL",
        tooltip="URL of the file to download",
    ),
    PropertyDef(
        "save_path",
        PropertyType.FILE_PATH,
        default="",
        label="Save Path",
        tooltip="Local file path to save to (supports {{variables}})",
        placeholder="C:/downloads/file.pdf",
        essential=True,  # Show when collapsed
    ),
    PropertyDef(
        "use_browser",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Browser Context",
        tooltip="Use browser context for download (for authenticated sites)",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        label="Timeout (ms)",
        tooltip="Download timeout in milliseconds",
        min_value=0,
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=True,
        label="Overwrite Existing",
        tooltip="Overwrite existing file if it exists",
    ),
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL Certificate",
        tooltip="Verify SSL certificate when downloading. Disable only for trusted internal sites with self-signed certificates.",
    ),
)
@node(category="browser")
class DownloadFileNode(BaseNode):
    """
    Download a file from URL to local path.

    Downloads any file (image, document, etc.) from a URL and saves it
    to a local file path. Supports both direct URL downloads and
    downloading through the browser context for authenticated sessions.

    Inputs:
        - url: URL of the file to download
        - filename: Optional filename override

    Outputs:
        - path: Full path where file was saved
        - size: File size in bytes
        - success: Whether download succeeded
    """

    # @category: browser
    # @requires: uiautomation
    # @ports: url, filename -> path, attachment_file, size, success

    def __init__(self, node_id: str, name: str = "Download File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DownloadFileNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("url", DataType.STRING)
        self.add_input_port("filename", DataType.STRING, required=False)
        self.add_output_port("path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)
        self.add_output_port("size", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Download file from URL."""
        import os
        import ssl
        import urllib.request
        from urllib.parse import unquote, urlparse

        try:
            url = self.get_parameter("url")
            filename_override = self.get_input_value("filename")

            # Resolve variables

            if not url:
                raise ValueError("URL is required")

            save_path = self.get_parameter("save_path", "")

            use_browser = self.get_parameter("use_browser", False)
            timeout = self.get_parameter("timeout", 30000)
            overwrite = self.get_parameter("overwrite", True)

            # Determine filename
            if filename_override:
                filename = filename_override
            else:
                # Extract filename from URL
                parsed = urlparse(url)
                filename = os.path.basename(unquote(parsed.path))
                if not filename or "." not in filename:
                    # Generate a filename based on URL hash
                    import hashlib

                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    # Try to guess extension from URL
                    ext = ".jpg"  # Default
                    url_lower = url.lower()
                    for e in [".png", ".gif", ".webp", ".svg", ".jpeg", ".bmp"]:
                        if e in url_lower:
                            ext = e
                            break
                    filename = f"download_{url_hash}{ext}"

            # Determine full save path
            if save_path:
                if os.path.isdir(save_path):
                    full_path = os.path.join(save_path, filename)
                else:
                    # save_path is the full file path
                    full_path = save_path
            else:
                # Default to downloads folder
                downloads_dir = os.path.expanduser("~/Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                full_path = os.path.join(downloads_dir, filename)

            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Check if file exists
            if os.path.exists(full_path) and not overwrite:
                # Add number suffix
                base, ext = os.path.splitext(full_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                full_path = f"{base}_{counter}{ext}"

            file_size = 0

            if use_browser:
                # Download using browser context (for authenticated sessions)
                page = context.get_active_page()
                if not page:
                    raise ValueError("No active page for browser download")

                # Use page.request to download
                response = await page.request.get(url, timeout=timeout)
                content = await response.body()

                with open(full_path, "wb") as f:
                    f.write(content)
                file_size = len(content)
            else:
                # Direct download using urllib (run in executor to not block)
                import asyncio

                verify_ssl = self.get_parameter("verify_ssl", True)

                def download_file():
                    # Create SSL context based on verify_ssl setting
                    if verify_ssl:
                        ctx = ssl.create_default_context()
                    else:
                        # WARNING: Disabling SSL verification is insecure
                        # Only use for trusted internal sites with self-signed certs
                        logger.warning(
                            f"SSL verification disabled for download from {url}. "
                            "This is insecure and should only be used for trusted internal sites."
                        )
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE

                    req = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        },
                    )
                    with urllib.request.urlopen(
                        req, timeout=timeout / 1000, context=ctx
                    ) as response:
                        content = response.read()
                        with open(full_path, "wb") as f:
                            f.write(content)
                        return len(content)

                loop = asyncio.get_event_loop()
                file_size = await loop.run_in_executor(None, download_file)

            # Set outputs
            self.set_output_value("path", full_path)
            self.set_output_value("attachment_file", [full_path])
            self.set_output_value("size", file_size)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Downloaded {url} to {full_path} ({file_size} bytes)")

            return {
                "success": True,
                "data": {"path": full_path, "size": file_size, "url": url},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            logger.error(f"Failed to download file: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
