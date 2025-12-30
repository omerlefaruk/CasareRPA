"""
Mass replace ui/theme imports with theme_system.
"""

import os
import re
from pathlib import Path

ROOT = Path(r"c:\Users\Rau\Desktop\CasareRPA\src")

# All patterns to replace
REPLACEMENTS = [
    # Main import pattern - replace whole line
    (
        r"from casare_rpa\.presentation\.canvas\.ui\.theme import[^\n]+",
        "from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS",
    ),
    # TYPE_COLORS usage
    (r'TYPE_COLORS\.get\(["\']Integer["\'],\s*[^)]+\)', "THEME.info"),
    (r'TYPE_COLORS\.get\(["\']String["\'],\s*[^)]+\)', "THEME.success"),
    (r'TYPE_COLORS\.get\(["\']Boolean["\'],\s*[^)]+\)', "THEME.info"),
    (r'TYPE_COLORS\.get\(["\']Float["\'],\s*[^)]+\)', "THEME.info"),
    (r'TYPE_COLORS\.get\(["\']List["\'],\s*[^)]+\)', "THEME.wire_list"),
    (r'TYPE_COLORS\.get\(["\']Dict["\'],\s*[^)]+\)', "THEME.wire_dict"),
    (r"TYPE_COLORS\.get\([^\)]+\)", "THEME.text_muted"),
    (r"TYPE_COLORS\[([^\]]+)\]", "THEME.text_muted"),
    (r"TYPE_COLORS", "{}"),
    # ANIMATIONS -> TOKENS.transitions
    (r"\bANIMATIONS\.instant\b", "TOKENS.transitions.instant"),
    (r"\bANIMATIONS\.fast\b", "TOKENS.transitions.fast"),
    (r"\bANIMATIONS\.normal\b", "TOKENS.transitions.normal"),
    (r"\bANIMATIONS\.medium\b", "TOKENS.transitions.medium"),
    (r"\bANIMATIONS\.slow\b", "TOKENS.transitions.slow"),
    (r"\bANIMATIONS\.emphasis\b", "TOKENS.transitions.slow"),
    (r"\bANIMATIONS\b", "TOKENS.transitions"),
    # DARK_CANVAS_COLORS -> THEME
    (r"DARK_CANVAS_COLORS\.(\w+)", r"THEME.\1"),
    (r"DARK_CANVAS_COLORS", "THEME"),
    # Theme class -> THEME
    (r"Theme\.get_colors\(\)\.(\w+)", r"THEME.\1"),
    (r"Theme\.get_colors\(\)", "THEME"),
    (r"Theme\.colors\.(\w+)", r"THEME.\1"),
    # SPACING -> TOKENS.spacing
    (r"\bSPACING\.xs\b", "TOKENS.spacing.xxs"),
    (r"\bSPACING\.sm\b", "TOKENS.spacing.xs"),
    (r"\bSPACING\.md\b", "TOKENS.spacing.sm"),
    (r"\bSPACING\.lg\b", "TOKENS.spacing.md"),
    (r"\bSPACING\.xl\b", "TOKENS.spacing.lg"),
    # FONT_SIZES -> TOKENS.typography
    (r"\bFONT_SIZES\.xs\b", "TOKENS.typography.caption"),
    (r"\bFONT_SIZES\.sm\b", "TOKENS.typography.body_sm"),
    (r"\bFONT_SIZES\.md\b", "TOKENS.typography.body"),
    (r"\bFONT_SIZES\.lg\b", "TOKENS.typography.body_lg"),
    (r"\bFONT_SIZES\.xl\b", "TOKENS.typography.heading_lg"),
    # BORDER_RADIUS -> TOKENS.radius
    (r"\bBORDER_RADIUS\.sm\b", "TOKENS.radius.sm"),
    (r"\bBORDER_RADIUS\.md\b", "TOKENS.radius.md"),
    (r"\bBORDER_RADIUS\.lg\b", "TOKENS.radius.lg"),
]

SKIP = ["__pycache__", ".pyc", "colors.py", "design_tokens.py"]


def is_markdown(filepath: Path) -> bool:
    return filepath.suffix == ".md"


def migrate_file(filepath: Path) -> tuple[bool, int]:
    if any(s in str(filepath) for s in SKIP):
        return False, 0

    if filepath.suffix not in [".py", ".md"]:
        return False, 0

    try:
        content = filepath.read_text(encoding="utf-8")
    except:
        return False, 0

    original = content
    count = 0

    for pattern, replacement in REPLACEMENTS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            count += 1
            content = new_content

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True, count

    return False, 0


def main():
    print("Replacing ui/theme imports with theme_system")

    modified = 0
    total = 0

    for filepath in ROOT.rglob("*"):
        if filepath.is_file():
            was_modified, count = migrate_file(filepath)
            if was_modified:
                modified += 1
                total += count
                print(f"  {filepath.relative_to(ROOT)}")

    print(f"\nMigrated {modified} files ({total} changes)")


if __name__ == "__main__":
    main()
