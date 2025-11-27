"""
Generate placeholder installer assets for CasareRPA.

Creates the required BMP and ICO files for Inno Setup:
- banner.bmp (164x314) - Wizard side banner
- wizard.bmp (55x58) - Small header icon
- icon.ico (multi-resolution) - Application icon
"""

from pathlib import Path

from PIL import Image, ImageDraw

# Blue theme color
PRIMARY_COLOR = (37, 99, 235)  # #2563EB
SECONDARY_COLOR = (30, 64, 175)  # Darker blue for gradient


def create_banner(output_path: Path) -> None:
    """Create the wizard banner (164x314 pixels)."""
    width, height = 164, 314
    img = Image.new("RGB", (width, height), PRIMARY_COLOR)
    draw = ImageDraw.Draw(img)

    # Simple gradient effect from top to bottom
    for y in range(height):
        ratio = y / height
        r = int(PRIMARY_COLOR[0] * (1 - ratio * 0.3))
        g = int(PRIMARY_COLOR[1] * (1 - ratio * 0.3))
        b = int(PRIMARY_COLOR[2] * (1 - ratio * 0.1))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    img.save(output_path, "BMP")
    print(f"Created: {output_path}")


def create_wizard_icon(output_path: Path) -> None:
    """Create the small wizard header icon (55x58 pixels)."""
    width, height = 55, 58
    img = Image.new("RGB", (width, height), PRIMARY_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw a simple "C" shape for CasareRPA
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 2 - 4

    # White circle outline
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        outline="white",
        width=3,
    )

    # Cut out the right side to make it look like a "C"
    draw.rectangle(
        [center_x + 2, center_y - radius // 2, width, center_y + radius // 2],
        fill=PRIMARY_COLOR,
    )

    img.save(output_path, "BMP")
    print(f"Created: {output_path}")


def create_icon(output_path: Path) -> None:
    """Create multi-resolution ICO file (16, 32, 48, 256 pixels)."""
    sizes = [16, 32, 48, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (*PRIMARY_COLOR, 255))
        draw = ImageDraw.Draw(img)

        # Draw a simple "C" shape
        center = size // 2
        radius = size // 2 - max(1, size // 16)
        line_width = max(1, size // 8)

        # White circle
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            outline="white",
            width=line_width,
        )

        # Cut out right side for "C" shape
        cut_height = radius // 2
        draw.rectangle(
            [center + line_width, center - cut_height, size, center + cut_height],
            fill=(*PRIMARY_COLOR, 255),
        )

        images.append(img)

    # Save as ICO with all sizes
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Created: {output_path}")


def main() -> None:
    """Generate all installer assets."""
    script_dir = Path(__file__).parent
    inno_dir = script_dir / "inno"
    inno_dir.mkdir(exist_ok=True)

    print("Generating installer assets...")
    print(f"Output directory: {inno_dir}")
    print()

    create_banner(inno_dir / "banner.bmp")
    create_wizard_icon(inno_dir / "wizard.bmp")
    create_icon(inno_dir / "icon.ico")

    print()
    print("All assets generated successfully!")


if __name__ == "__main__":
    main()
