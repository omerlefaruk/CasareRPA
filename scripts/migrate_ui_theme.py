"""
Migrate all ui/theme.py imports to theme_system and delete ui/theme.py
"""

import os
import re
from pathlib import Path

ROOT = Path(r"c:\Users\Rau\Desktop\CasareRPA\src")

# Import pattern replacements
IMPORT_REPLACEMENTS = [
    # Full module imports
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import .*', 
     'from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS'),
    
    # Specific imports we need to handle
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import THEME\b',
     'from casare_rpa.presentation.canvas.theme_system import THEME'),
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import Theme\b',
     'from casare_rpa.presentation.canvas.theme_system import THEME'),
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import ANIMATIONS\b',
     'from casare_rpa.presentation.canvas.theme_system import TOKENS'),
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import TYPE_COLORS\b',
     'from casare_rpa.presentation.canvas.theme_system import THEME'),
    (r'from casare_rpa\.presentation\.canvas\.ui\.theme import DARK_CANVAS_COLORS\b',
     'from casare_rpa.presentation.canvas.theme_system import THEME'),
]

# Usage replacements
USAGE_REPLACEMENTS = [
    # Theme class usage -> THEME instance
    (r'\bTheme\.get_colors\(\)', 'THEME'),
    (r'\bTheme\.colors\(\)', 'THEME'),
    (r'\bTheme\.colors\.', 'THEME.'),
    (r'\bTheme\.get_spacing\(\)', 'TOKENS.spacing'),
    (r'\bTheme\.get_animations\(\)', 'TOKENS.transitions'),
    (r'\bTheme\.get_radii\(\)', 'TOKENS.radius'),
    (r'\bTheme\.get_button_sizes\(\)', 'TOKENS.sizes'),
    (r'\bTheme\.get_icon_sizes\(\)', 'TOKENS.sizes'),
    (r'\bTheme\.get_font_sizes\(\)', 'TOKENS.typography'),
    
    # DARK_CANVAS_COLORS -> THEME
    (r'\bDARK_CANVAS_COLORS\.', 'THEME.'),
    
    # ANIMATIONS -> TOKENS.transitions
    (r'\bANIMATIONS\.instant\b', 'TOKENS.transitions.instant'),
    (r'\bANIMATIONS\.fast\b', 'TOKENS.transitions.fast'),
    (r'\bANIMATIONS\.normal\b', 'TOKENS.transitions.normal'),
    (r'\bANIMATIONS\.medium\b', 'TOKENS.transitions.medium'),
    (r'\bANIMATIONS\.slow\b', 'TOKENS.transitions.slow'),
    (r'\bANIMATIONS\.emphasis\b', 'TOKENS.transitions.slow'),
    
    # TYPE_COLORS -> THEME wire colors
    (r'\bTYPE_COLORS\[', 'THEME.wire_'),
    (r"TYPE_COLORS\.get\(['\"](\w+)['\"]", r'THEME.wire_\1'),
]

SKIP = ["__pycache__", ".pyc"]


def migrate_file(filepath: Path) -> tuple[bool, int]:
    if any(s in str(filepath) for s in SKIP) or filepath.suffix != ".py":
        return False, 0
    
    # Skip the ui/theme.py itself
    if "ui\\theme.py" in str(filepath) or "ui/theme.py" in str(filepath):
        return False, 0
    
    try:
        content = filepath.read_text(encoding="utf-8")
    except:
        return False, 0
    
    original = content
    count = 0
    
    # Replace imports first
    for pattern, replacement in IMPORT_REPLACEMENTS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            count += 1
            content = new_content
    
    # Replace usages
    for pattern, replacement in USAGE_REPLACEMENTS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            count += 1
            content = new_content
    
    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True, count
    
    return False, 0


def main():
    print("=" * 60)
    print("UI Theme Migration")
    print("=" * 60)
    
    py_files = list(ROOT.rglob("*.py"))
    
    modified = 0
    total = 0
    
    for filepath in py_files:
        was_modified, count = migrate_file(filepath)
        if was_modified:
            modified += 1
            total += count
            print(f"  {filepath.relative_to(ROOT)}: {count}")
    
    print(f"\nMigrated {modified} files ({total} changes)")
    
    # Delete ui/theme.py
    ui_theme = ROOT / "casare_rpa" / "presentation" / "canvas" / "ui" / "theme.py"
    if ui_theme.exists():
        ui_theme.unlink()
        print(f"\nDeleted: {ui_theme.relative_to(ROOT)}")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
