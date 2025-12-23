"""
Tests for ImageConvertNode.

Covers single-file and folder (batch) conversion behavior.
"""

from pathlib import Path

import pytest

from casare_rpa.nodes.file.image_nodes import ImageConvertNode


class TestImageConvertNode:
    @pytest.mark.asyncio
    async def test_batch_convert_folder_defaults_to_converted_subdir(
        self, execution_context, tmp_path: Path
    ) -> None:
        from PIL import Image

        source_dir = tmp_path / "images"
        source_dir.mkdir()
        Image.new("RGB", (10, 10), color="red").save(source_dir / "a.png", "PNG")
        Image.new("RGB", (10, 10), color="blue").save(source_dir / "b.png", "PNG")

        node = ImageConvertNode(
            "test_convert",
            config={
                "source_path": str(source_dir),
                "output_format": "WEBP",
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("format") == "WEBP"
        assert node.get_output_value("file_count") == 2
        files = node.get_output_value("files")
        assert isinstance(files, list)
        assert len(files) == 2

        output_dir = Path(node.get_output_value("output_path"))
        assert output_dir == source_dir / "converted"
        assert (output_dir / "a.webp").exists()
        assert (output_dir / "b.webp").exists()

    @pytest.mark.asyncio
    async def test_scale_percent_resizes_output(self, execution_context, tmp_path: Path) -> None:
        from PIL import Image

        source_file = tmp_path / "big.png"
        Image.new("RGB", (100, 80), color="red").save(source_file, "PNG")

        output_file = tmp_path / "small.jpg"
        node = ImageConvertNode(
            "test_convert",
            config={
                "source_path": str(source_file),
                "output_path": str(output_file),
                "output_format": "JPEG",
                "scale_percent": "50%",
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        with Image.open(output_file) as img:
            assert img.size == (50, 40)
