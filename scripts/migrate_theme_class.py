"""
Replace all Theme.* method calls with direct THEME.* attribute access.
"""

import os
import re
from pathlib import Path

ROOT = Path(r"c:\Users\Rau\Desktop\CasareRPA\src")

# Pattern replacements
REPLACEMENTS = [
    # Theme class methods -> direct THEME access
    (r'Theme\.get_colors\(\)', 'THEME'),
    (r'Theme\.colors\(\)', 'THEME'),
    (r'Theme\.get_status_qcolor\(["\']success["\']\)', 'QColor(THEME.success)'),
    (r'Theme\.get_status_qcolor\(["\']error["\']\)', 'QColor(THEME.error)'),
    (r'Theme\.get_status_qcolor\(["\']warning["\']\)', 'QColor(THEME.warning)'),
    (r'Theme\.get_status_qcolor\(["\']disabled["\']\)', 'QColor(THEME.text_disabled)'),
    (r'Theme\.get_status_qcolor\(["\']skipped["\']\)', 'QColor(THEME.node_skipped)'),
    (r'Theme\.get_status_qcolor\(["\']running["\']\)', 'QColor(THEME.node_running)'),
    (r'Theme\.get_status_qcolor\(["\']idle["\']\)', 'QColor(THEME.node_idle)'),
    (r'Theme\.get_status_qcolor\(([^)]+)\)', r'QColor(THEME.success)'),
    
    (r'Theme\.get_node_border_qcolor\(["\']normal["\']\)', 'QColor(THEME.border)'),
    (r'Theme\.get_node_border_qcolor\(["\']selected["\']\)', 'QColor(THEME.primary)'),
    (r'Theme\.get_node_border_qcolor\(["\']running["\']\)', 'QColor(THEME.warning)'),
    (r'Theme\.get_node_border_qcolor\([^)]+\)', 'QColor(THEME.border)'),
    
    (r'Theme\.get_node_bg_qcolor\(\)', 'QColor(THEME.bg_surface)'),
    
    (r'Theme\.get_canvas_colors\(\)', 'THEME'),
    
    (r'Theme\.get_category_qcolor\(([^)]+)\)', r'QColor(THEME.primary)'),
    
    (r'Theme\.get_badge_colors\(\)', '(THEME.bg_component, THEME.text_primary, THEME.border)'),
    
    # cc.* -> THEME.* (after get_canvas_colors)
    (r'\bcc\.node_text_secondary\b', 'THEME.text_secondary'),
    (r'\bcc\.node_text_port\b', 'THEME.text_muted'),
    (r'\bcc\.category_database\b', 'THEME.info'),
    (r'\bcc\.category_triggers\b', 'THEME.primary'),
    (r'\bcc\.collapse_btn_bg\b', 'THEME.bg_component'),
    (r'\bcc\.collapse_btn_symbol\b', 'THEME.text_primary'),
    (r'\bcc\.node_bg\b', 'THEME.bg_surface'),
    (r'\bcc\.node_border\b', 'THEME.border'),
    (r'\bcc\.wire_', 'THEME.wire_'),
    (r'\bcc\.', 'THEME.'),
    
    # Theme class static access
    (r'\bTheme\.', 'THEME.'),
]

SKIP = ["__pycache__", ".pyc", "colors.py", "design_tokens.py"]


def migrate_file(filepath: Path) -> tuple[bool, int]:
    if any(s in str(filepath) for s in SKIP) or filepath.suffix != ".py":
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
    print("Migrating Theme.* to THEME.*")
    
    modified = 0
    total = 0
    
    for filepath in ROOT.rglob("*.py"):
        was_modified, count = migrate_file(filepath)
        if was_modified:
            modified += 1
            total += count
            print(f"  {filepath.relative_to(ROOT)}: {count}")
    
    print(f"\nMigrated {modified} files ({total} changes)")


if __name__ == "__main__":
    main()
