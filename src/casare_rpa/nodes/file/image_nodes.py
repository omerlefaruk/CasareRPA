"""
Image conversion nodes for CasareRPA.

This module provides nodes for image format conversion:
- ImageConvertNode: Convert images between formats (PNG, JPEG, WEBP, BMP, GIF)

SECURITY: All file operations are subject to path sandboxing.
"""

import os
import asyncio
from pathlib import Path

from loguru import logger
from PIL import Image, ImageOps

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

SUPPORTED_INPUT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
}

SCALE_PERCENT_CHOICES = ["5%", "10%", "25%", "50%", "75%", "100%"]


@properties(
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        required=True,
        label="Source Path",
        tooltip="Path to an image file OR a folder (batch convert)",
        placeholder="C:\\path\\to\\image.png or C:\\path\\to\\images",
    ),
    PropertyDef(
        "output_path",
        PropertyType.STRING,
        required=False,
        label="Output Path",
        tooltip="Destination file path or directory (auto-generated if empty)",
        placeholder="C:\\path\\to\\output.jpg or C:\\path\\to\\output\\",
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
        "scale_percent",
        PropertyType.CHOICE,
        default="100%",
        label="Scale (%)",
        tooltip="Resize output dimensions to this percentage of original",
        choices=SCALE_PERCENT_CHOICES,
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="When source_path is a folder, convert images in subfolders too",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories",
    ),
)
@node(category="file")
class ImageConvertNode(BaseNode):
    """
    Convert an image to a different format.

    Config (via @properties):
        source_path: Source image path (required)
        output_path: Destination path (optional, auto-generated if empty)
        output_format: Target format - PNG, JPEG, WEBP, BMP, GIF (default: JPEG)
        quality: JPEG/WEBP quality 1-100 (default: 85)
        scale_percent: Resize output dimensions (default: 100%)
        overwrite: Overwrite if destination exists (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        source_path: Source path override (if connected)

    Outputs:
        output_path: Path to converted image
        files: Converted file paths (batch only)
        file_count: Number of converted files (batch only)
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
        self.add_output_port("files", DataType.LIST)
        self.add_output_port("file_count", DataType.INTEGER)
        self.add_output_port("format", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_parameter("source_path")
            output_path = self.get_parameter("output_path", "")
            output_format = self.get_parameter("output_format", "JPEG")
            quality = self.get_parameter("quality", 85)
            scale_percent = self.get_parameter("scale_percent", "100%")
            overwrite = self.get_parameter("overwrite", False)
            recursive = self.get_parameter("recursive", False)
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

            try:
                quality = int(quality)
            except (TypeError, ValueError):
                raise ValueError("quality must be an integer between 1 and 100")

            if quality < 1 or quality > 100:
                raise ValueError("quality must be between 1 and 100")

            try:
                if isinstance(scale_percent, str):
                    scale_percent = scale_percent.strip()
                    if scale_percent.endswith("%"):
                        scale_percent = scale_percent[:-1]
                scale_percent = int(scale_percent)
            except (TypeError, ValueError):
                raise ValueError(
                    "scale_percent must be one of: " + ", ".join(SCALE_PERCENT_CHOICES)
                )

            if scale_percent not in (5, 10, 25, 50, 75, 100):
                raise ValueError(
                    "scale_percent must be one of: " + ", ".join(SCALE_PERCENT_CHOICES)
                )

            # Resolve variables and environment in source path
            source_path = context.resolve_value(source_path)
            source_path = os.path.expandvars(source_path)

            # SECURITY: Validate source path
            source = validate_path_security(source_path, "read", allow_dangerous)

            if not source.exists():
                raise FileNotFoundError(f"Source image not found: {source_path}")

            ext = SUPPORTED_FORMATS[output_format]

            if source.is_dir():
                if output_path:
                    output_path = context.resolve_value(output_path)
                    output_path = os.path.expandvars(output_path)
                else:
                    output_path = str(source / "converted")

                output_dir = validate_path_security(
                    output_path, "write", allow_dangerous
                )
                if output_dir.exists() and output_dir.is_file():
                    raise ValueError(
                        f"output_path must be a directory when source_path is a folder: {output_path}"
                    )
                output_dir.mkdir(parents=True, exist_ok=True)

                candidates = source.rglob("*") if recursive else source.iterdir()
                input_files = [
                    p
                    for p in candidates
                    if p.is_file() and p.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS
                ]
                if not input_files:
                    raise ValueError(f"No images found in folder: {source}")

                logger.info(
                    f"Batch converting {len(input_files)} images: {source} -> {output_dir} ({output_format})"
                )

                def _convert_batch() -> list[str]:
                    converted: list[str] = []
                    resample = (
                        Image.Resampling.LANCZOS
                        if hasattr(Image, "Resampling")
                        else Image.LANCZOS
                    )
                    for input_file in input_files:
                        safe_source = validate_path_security(
                            input_file, "read", allow_dangerous
                        )
                        rel = (
                            input_file.relative_to(source)
                            if recursive
                            else Path(input_file.name)
                        )
                        dest_candidate = (output_dir / rel).with_suffix(ext)
                        dest_candidate.parent.mkdir(parents=True, exist_ok=True)
                        dest = validate_path_security(
                            dest_candidate, "write", allow_dangerous
                        )

                        if dest.exists() and not overwrite:
                            raise FileExistsError(
                                f"Destination already exists: {dest_candidate}"
                            )

                        with Image.open(safe_source) as img:
                            img = ImageOps.exif_transpose(img)

                            if scale_percent != 100:
                                new_width = max(
                                    1, int(round(img.width * scale_percent / 100))
                                )
                                new_height = max(
                                    1, int(round(img.height * scale_percent / 100))
                                )
                                img = img.resize(
                                    (new_width, new_height), resample=resample
                                )

                            if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                                background = Image.new("RGB", img.size, (255, 255, 255))
                                if img.mode == "P":
                                    img = img.convert("RGBA")
                                background.paste(img, mask=img.split()[3])
                                img = background
                            elif output_format == "JPEG" and img.mode != "RGB":
                                img = img.convert("RGB")

                            save_kwargs = {}
                            if output_format in ("JPEG", "WEBP"):
                                save_kwargs["quality"] = quality
                            if output_format in ("PNG", "JPEG"):
                                save_kwargs["optimize"] = True

                            img.save(dest, format=output_format, **save_kwargs)

                        converted.append(str(dest))

                    return converted

                converted_files = await asyncio.to_thread(_convert_batch)

                self.set_output_value("output_path", str(output_dir))
                self.set_output_value("files", converted_files)
                self.set_output_value("file_count", len(converted_files))
                self.set_output_value("format", output_format)
                self.set_output_value("success", True)
                self.status = NodeStatus.SUCCESS

                return {
                    "success": True,
                    "data": {
                        "output_path": str(output_dir),
                        "format": output_format,
                        "file_count": len(converted_files),
                    },
                    "next_nodes": ["exec_out"],
                }

            # Generate output path if not specified
            if not output_path:
                output_path = str(source.with_suffix(ext))
                if not overwrite and Path(output_path).resolve() == source.resolve():
                    output_path = str(source.with_name(f"{source.stem}_converted{ext}"))
            else:
                output_path = context.resolve_value(output_path)
                output_path = os.path.expandvars(output_path)

            # SECURITY: Validate output path (supports directory targets)
            directory_hint = output_path.endswith(os.sep) or (
                os.altsep is not None and output_path.endswith(os.altsep)
            )
            dest_candidate = validate_path_security(
                output_path, "write", allow_dangerous
            )
            if directory_hint or (dest_candidate.exists() and dest_candidate.is_dir()):
                dest_candidate.mkdir(parents=True, exist_ok=True)
                dest_candidate = dest_candidate / f"{source.stem}{ext}"

            dest = validate_path_security(dest_candidate, "write", allow_dangerous)

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {output_path}")

            # Create output directory if needed
            if dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Converting image: {source} -> {dest} ({output_format})")

            def _convert_image() -> None:
                """Convert image synchronously (runs in thread)."""
                with Image.open(source) as img:
                    img = ImageOps.exif_transpose(img)

                    if scale_percent != 100:
                        resample = (
                            Image.Resampling.LANCZOS
                            if hasattr(Image, "Resampling")
                            else Image.LANCZOS
                        )
                        new_width = max(1, int(round(img.width * scale_percent / 100)))
                        new_height = max(
                            1, int(round(img.height * scale_percent / 100))
                        )
                        img = img.resize((new_width, new_height), resample=resample)

                    # Handle transparency for JPEG (convert RGBA to RGB)
                    if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(img, mask=img.split()[3])  # alpha as mask
                        img = background
                    elif output_format == "JPEG" and img.mode != "RGB":
                        img = img.convert("RGB")

                    save_kwargs = {}
                    if output_format in ("JPEG", "WEBP"):
                        save_kwargs["quality"] = quality
                    if output_format in ("PNG", "JPEG"):
                        save_kwargs["optimize"] = True

                    img.save(dest, format=output_format, **save_kwargs)

            await asyncio.to_thread(_convert_image)

            self.set_output_value("output_path", str(dest))
            self.set_output_value("files", [str(dest)])
            self.set_output_value("file_count", 1)
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
