"""
Image conversion nodes for CasareRPA.

This module provides nodes for image format conversion:
- ImageConvertNode: Convert images between formats (PNG, JPEG, WEBP, BMP, GIF)

SECURITY: All file operations are subject to path sandboxing.
"""

import os
from pathlib import Path

from loguru import logger
from PIL import Image

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
)


# Supported formats and their file extensions
SUPPORTED_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "GIF": ".gif",
}


@node(category="file")
@properties(
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        required=True,
        label="Source Path",
        tooltip="Path to the image to convert",
        placeholder="C:\\path\\to\\image.png",
    ),
    PropertyDef(
        "output_path",
        PropertyType.STRING,
        required=False,
        label="Output Path",
        tooltip="Destination path (auto-generated if empty)",
        placeholder="C:\\path\\to\\output.jpg",
    ),
    PropertyDef(
        "output_format",
        PropertyType.CHOICE,
        default="JPEG",
        label="Output Format",
        tooltip="Target image format",
        choices=["PNG", "JPEG", "WEBP", "BMP", "GIF"],
    ),
    PropertyDef(
        "quality",
        PropertyType.INTEGER,
        default=85,
        label="Quality",
        tooltip="Quality for JPEG/WEBP (1-100)",
        min_value=1,
        max_value=100,
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories",
    ),
)
class ImageConvertNode(BaseNode):
    """
    Convert an image to a different format.

    Config (via @properties):
        source_path: Source image path (required)
        output_path: Destination path (optional, auto-generated if empty)
        output_format: Target format - PNG, JPEG, WEBP, BMP, GIF (default: JPEG)
        quality: JPEG/WEBP quality 1-100 (default: 85)
        overwrite: Overwrite if destination exists (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        source_path: Source path override (if connected)

    Outputs:
        output_path: Path to converted image
        format: Output format used
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: PIL/Pillow
    # @ports: source_path -> output_path, format, success

    def __init__(self, node_id: str, name: str = "Image Convert", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ImageConvertNode"

    def _define_ports(self) -> None:
        self.add_input_port("source_path", DataType.STRING)
        self.add_output_port("output_path", DataType.STRING)
        self.add_output_port("format", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_parameter("source_path")
            output_path = self.get_parameter("output_path", "")
            output_format = self.get_parameter("output_format", "JPEG")
            quality = self.get_parameter("quality", 85)
            overwrite = self.get_parameter("overwrite", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not source_path:
                raise ValueError("source_path is required")

            # Validate format
            output_format = output_format.upper()
            if output_format not in SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported format: {output_format}. "
                    f"Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
                )

            # Resolve variables and environment in source path
            source_path = context.resolve_value(source_path)
            source_path = os.path.expandvars(source_path)

            # SECURITY: Validate source path
            source = validate_path_security(source_path, "read", allow_dangerous)

            if not source.exists():
                raise FileNotFoundError(f"Source image not found: {source_path}")

            # Generate output path if not specified
            if not output_path:
                ext = SUPPORTED_FORMATS[output_format]
                output_path = str(source.with_suffix(ext))
            else:
                output_path = context.resolve_value(output_path)
                output_path = os.path.expandvars(output_path)

            # SECURITY: Validate output path
            dest = validate_path_security(output_path, "write", allow_dangerous)

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {output_path}")

            # Create output directory if needed
            if dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

            # Load and convert image
            logger.info(f"Converting image: {source} -> {dest} ({output_format})")

            with Image.open(source) as img:
                # Handle transparency for JPEG (convert RGBA to RGB)
                if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[3])  # Use alpha as mask
                    img = background
                elif output_format == "JPEG" and img.mode != "RGB":
                    img = img.convert("RGB")

                # Save with appropriate options
                save_kwargs = {}
                if output_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                if output_format == "PNG":
                    save_kwargs["optimize"] = True

                img.save(dest, format=output_format, **save_kwargs)

            self.set_output_value("output_path", str(dest))
            self.set_output_value("format", output_format)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"output_path": str(dest), "format": output_format},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in ImageConvertNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Error in ImageConvertNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
