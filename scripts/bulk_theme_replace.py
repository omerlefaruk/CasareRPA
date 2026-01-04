"""
Bulk Theme Replace Script for CasareRPA.
Replaces ALL hardcoded UI values with theme tokens.

Usage: python scripts/bulk_theme_replace.py
"""

import re
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src" / "casare_rpa" / "presentation" / "canvas"


# Comprehensive replacement patterns
PATTERNS = {
    # === Size/Margin/Spacing Method Calls ===
    r'\.setFixedSize\((\d+),\s*(\d+)\)': r'set_fixed_size(widget, \1, \2)',
    r'\.setMinimumSize\((\d+),\s*(\d+)\)': r'set_min_size(widget, \1, \2)',
    r'\.setMaximumSize\((\d+),\s*(\d+)\)': r'set_max_size(widget, \1, \2)',
    r'\.setMinimumWidth\((\d+)\)': r'set_min_width(widget, \1)',
    r'\.setMaximumWidth\((\d+)\)': r'set_max_width(widget, \1)',
    r'\.setMinimumHeight\((\d+)\)': r'set_min_height(widget, \1)',
    r'\.setMaximumHeight\((\d+)\)': r'set_max_height(widget, \1)',
    r'\.setFixedWidth\((\d+)\)': r'set_fixed_width(widget, \1)',
    r'\.setFixedHeight\((\d+)\)': r'set_fixed_height(widget, \1)',
    r'\.resize\((\d+),\s*(\d+)\)': r'set_fixed_size(widget, \1, \2)',
    r'\.setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)': r'set_margins(layout, (\1, \2, \3, \4))',
    r'\.setSpacing\((\d+)\)': r'set_spacing(layout, \1)',
    r'\.setMargin\((\d+)\)': r'set_margins(layout, (\1, \1, \1, \1))',

    # === Common Size Values → TOKENS ===
    r'\b(400|500|600),\s*(300|400|500)\)': r'(TOKENS.sizes.dialog_width_sm, TOKENS.sizes.dialog_height_sm)',
    r'\b600,\s*500\b': r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)',
    r'\b800,\s*600\b': r'(TOKENS.sizes.dialog_width_lg, TOKENS.sizes.dialog_height_lg)',
    r'\b1000,\s*700\b': r'(TOKENS.sizes.dialog_width_xl, TOKENS.sizes.dialog_height_xl)',

    # Panel sizes
    r'\b200\b': r'TOKENS.sizes.panel_width_min',
    r'\b250\b': r'TOKENS.sizes.panel_width_default',
    r'\b300\b': r'TOKENS.sizes.panel_width_default',
    r'\b400\b': r'TOKENS.sizes.panel_width_max',
    r'\b600\b': r'TOKENS.sizes.panel_width_max',

    # Button sizes
    r'\b80\b': r'TOKENS.sizes.button_min_width',
    r'\b100\b': r'TOKENS.sizes.button_width_sm',
    r'\b120\b': r'TOKENS.sizes.combo_width_lg',

    # Input sizes
    r'\b150\b': r'TOKENS.sizes.combo_width_md',
    r'\b24\b': r'TOKENS.sizes.input_height_sm',
    r'\b28\b': r'TOKENS.sizes.input_height_md',
    r'\b32\b': r'TOKENS.sizes.button_height_lg',

    # === Spacing Values in setSpacing/setContentsMargins ===
    r'setSpacing\(4\)': r'set_spacing(layout, TOKENS.spacing.sm)',
    r'setSpacing\(8\)': r'set_spacing(layout, TOKENS.spacing.md)',
    r'setSpacing\(12\)': r'set_spacing(layout, TOKENS.spacing.lg)',
    r'setSpacing\(16\)': r'set_spacing(layout, TOKENS.spacing.xl)',

    # Margins
    r'setContentsMargins\(\(0, 0, 0, 0\)\)': r'set_margins(layout, TOKENS.margins.none)',
    r'setContentsMargins\(\(4, 4, 4, 4\)\)': r'set_margins(layout, TOKENS.margins.tight)',
    r'setContentsMargins\(\(8, 8, 8, 8\)\)': r'set_margins(layout, TOKENS.margins.compact)',
    r'setContentsMargins\(\(12, 12, 12, 12\)\)': r'set_margins(layout, TOKENS.margins.standard)',
    r'setContentsMargins\(\(16, 16, 16, 16\)\)': r'set_margins(layout, TOKENS.margins.comfortable)',

    # === StyleSheet px values → TOKENS ===
    # Border radius
    r'border-radius:\s*2px': r'border-radius: {TOKENS.radii.xs}px',
    r'border-radius:\s*3px': r'border-radius: {TOKENS.radii.xs}px',
    r'border-radius:\s*4px': r'border-radius: {TOKENS.radii.sm}px',
    r'border-radius:\s*6px': r'border-radius: {TOKENS.radii.md}px',
    r'border-radius:\s*8px': r'border-radius: {TOKENS.radii.md}px',
    r'border-radius:\s*10px': r'border-radius: {TOKENS.radii.lg}px',
    r'border-radius:\s*12px': r'border-radius: {TOKENS.radii.lg}px',

    # Padding
    r'padding:\s*2px': r'padding: {TOKENS.spacing.xs}px',
    r'padding:\s*4px': r'padding: {TOKENS.spacing.sm}px',
    r'padding:\s*6px': r'padding: {TOKENS.spacing.sm}px',
    r'padding:\s*8px': r'padding: {TOKENS.spacing.md}px',
    r'padding:\s*10px': r'padding: {TOKENS.spacing.md}px',
    r'padding:\s*12px': r'padding: {TOKENS.spacing.lg}px',
    r'padding:\s*16px': r'padding: {TOKENS.spacing.xl}px',

    # Padding with left/right
    r'padding:\s*0 4px': r'padding: 0 {TOKENS.spacing.sm}px',
    r'padding:\s*0 8px': r'padding: 0 {TOKENS.spacing.md}px',
    r'padding:\s*0 12px': r'padding: 0 {TOKENS.spacing.lg}px',
    r'padding:\s*0 16px': r'padding: 0 {TOKENS.spacing.xl}px',
    r'padding:\s*4px 8px': r'padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px',
    r'padding:\s*6px 12px': r'padding: {TOKENS.spacing.sm}px {TOKENS.spacing.lg}px',
    r'padding:\s*8px 16px': r'padding: {TOKENS.spacing.md}px {TOKENS.spacing.xl}px',

    # Margin
    r'margin:\s*4px': r'margin: {TOKENS.spacing.sm}px',
    r'margin:\s*8px': r'margin: {TOKENS.spacing.md}px',
    r'margin:\s*12px': r'margin: {TOKENS.spacing.lg}px',
    r'margin:\s*16px': r'margin: {TOKENS.spacing.xl}px',

    # Font sizes
    r"font-size:\s*10px": r"font-size: {TOKENS.fonts.xs}px",
    r"font-size:\s*11px": r"font-size: {TOKENS.fonts.sm}px",
    r"font-size:\s*12px": r"font-size: {TOKENS.fonts.md}px",
    r"font-size:\s*13px": r"font-size: {TOKENS.fonts.md}px",
    r"font-size:\s*14px": r"font-size: {TOKENS.fonts.lg}px",
    r"font-size:\s*16px": r"font-size: {TOKENS.fonts.xl}px",
    r"font-size:\s*18px": r"font-size: {TOKENS.fonts.xl}px",
    r"font-size:\s*20px": r"font-size: {TOKENS.fonts.xxl}px",

    # Width/Height in stylesheets
    r'min-width:\s*80px': r'min-width: {TOKENS.sizes.button_min_width}px',
    r'min-width:\s*100px': r'min-width: {TOKENS.sizes.button_width_sm}px',
    r'min-width:\s*120px': r'min-width: {TOKENS.sizes.combo_width_lg}px',
    r'min-width:\s*150px': r'min-width: {TOKENS.sizes.combo_width_md}px',
    r'min-width:\s*200px': r'min-width: {TOKENS.sizes.panel_width_min}px',
    r'min-height:\s*24px': r'min-height: {TOKENS.sizes.input_height_sm}px',
    r'min-height:\s*28px': r'min-height: {TOKENS.sizes.input_height_md}px',
    r'min-height:\s*32px': r'min-height: {TOKENS.sizes.button_height_lg}px',
    r'max-width:\s*200px': r'max-width: {TOKENS.sizes.panel_width_min}px',
    r'max-width:\s*300px': r'max-width: {TOKENS.sizes.panel_width_default}px',
    r'max-width:\s*400px': r'max-width: {TOKENS.sizes.panel_width_max}px',

    # === Hardcoded Colors → THEME ===
    # Note: These should use THEME constants from theme.py
    r'#1e1e1e': r'{THEME.bg_darkest}',
    r'#252526': r'{THEME.bg_dark}',
    r'#2d2d30': r'{THEME.bg_medium}',
    r'#333333': r'{THEME.bg_medium}',
    r'#3c3c3c': r'{THEME.bg_light}',
    r'#f0f0f0': r'{THEME.bg_light}',
    r'#ffffff': r'{THEME.bg_lightest}',

    # Text colors
    r'#cccccc': r'{THEME.text_muted}',
    r'#aaaaaa': r'{THEME.text_disabled}',
    r'#e0e0e0': r'{THEME.text_secondary}',
    r'#ffffff(?!\w)': r'{THEME.text_primary}',

    # Accent colors
    r'#007acc': r'{THEME.accent_primary}',
    r'#0078d4': r'{THEME.accent_primary}',
    r'#106ebe': r'{THEME.accent_secondary}',

    # Status colors
    r'#4caf50': r'{THEME.status_success}',
    r'#8bc34a': r'{THEME.status_success}',
    r'#ff9800': r'{THEME.status_warning}',
    r'#ff5722': r'{THEME.status_error}',
    r'#2196f3': r'{THEME.status_info}',

    # Border colors
    r'#3e3e42': r'{THEME.border}',
    r'#454545': r'{THEME.border}',
    r'#555555': r'{THEME.border}',

    # QSS-specific color patterns
    r'background:\s*rgb\(30,\s*30,\s*30\)': r'background: {THEME.bg_darkest}',
    r'background:\s*rgb\(37,\s*37,\s*38\)': r'background: {THEME.bg_dark}',
    r'background:\s*#1e1e1e': r'background: {THEME.bg_darkest}',
    r'background:\s*#252526': r'background: {THEME.bg_dark}',
    r'background:\s*#2d2d30': r'background: {THEME.bg_medium}',
    r'background:\s*#3c3c3c': r'background: {THEME.bg_light}',
    r'background:\s*white(?!\w)': r'background: {THEME.bg_lightest}',

    r'color:\s*rgb\(204,\s*204,\s*204\)': r'color: {THEME.text_muted}',
    r'color:\s*rgb\(170,\s*170,\s*170\)': r'color: {THEME.text_disabled}',
    r'color:\s*#cccccc': r'color: {THEME.text_muted}',
    r'color:\s*#aaaaaa': r'color: {THEME.text_disabled}',
    r'color:\s*#e0e0e0': r'color: {THEME.text_secondary}',
    r'color:\s*white(?!\w)': r'color: {THEME.text_primary}',

    r'border:\s*1px solid #3e3e42': r'border: 1px solid {THEME.border}',
    r'border:\s*1px solid #454545': r'border: 1px solid {THEME.border}',
    r'border:\s*1px solid #555555': r'border: 1px solid {THEME.border}',
    r'border:\s*1px solid rgb\(62,\s*62,\s*66\)': r'border: 1px solid {THEME.border}',

    # === Icon sizes ===
    r'\.setIconSize\(QSize\(16,\s*16\)\)': r'.setIconSize(QSize(TOKENS.sizes.icon_sm, TOKENS.sizes.icon_sm))',
    r'\.setIconSize\(QSize\(20,\s*20\)\)': r'.setIconSize(QSize(TOKENS.sizes.icon_md, TOKENS.sizes.icon_md))',
    r'\.setIconSize\(QSize\(24,\s*24\)\)': r'.setIconSize(QSize(TOKENS.sizes.icon_lg, TOKENS.sizes.icon_lg))',
    r'\.setIconSize\(QSize\(32,\s*32\)\)': r'.setIconSize(QSize(TOKENS.sizes.icon_xl, TOKENS.sizes.icon_xl))',

    # === Toolbar icon size ===
    r'\.setIconSize\(QSize\(24,\s*24\)\)': r'.setIconSize(QSize(TOKENS.sizes.toolbar_icon_size, TOKENS.sizes.toolbar_icon_size))',

    # === Checkbox/Radio sizes ===
    r'width:\s*18px': r'width: {TOKENS.sizes.checkbox_size}px',
    r'height:\s*18px': r'height: {TOKENS.sizes.checkbox_size}px',
}


def add_imports(content: str, filepath: Path) -> str:
    """Add required imports if not present."""
    lines = content.split('\n')

    # Check if theme imports already exist
    has_tokens_import = any('TOKENS' in line for line in lines)
    has_helpers_import = any('theme.helpers' in line for line in lines)
    has_theme_import = any('from casare_rpa.presentation.canvas.theme import THEME' in line or 'from casare_rpa.presentation.canvas.ui.theme import THEME' in line for line in lines)

    # Find import insertion point (after existing imports, before first class/def)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_idx = i + 1
        elif line.startswith('class ') or line.startswith('def '):
            break

    if insert_idx > 0:
        new_imports = []
        if not has_theme_import:
            new_imports.append('from casare_rpa.presentation.canvas.theme import THEME')
        if not has_tokens_import and ('TOKENS' in content or '{TOKENS' in content):
            new_imports.append('from casare_rpa.presentation.canvas.theme import TOKENS')
        if not has_helpers_import and any(f in content for f in ['set_fixed_size', 'set_min_size', 'set_margins', 'set_spacing']):
            new_imports.append('from casare_rpa.presentation.canvas.theme.helpers import set_fixed_size, set_min_size, set_max_size, set_margins, set_spacing, set_min_width, set_max_width, set_fixed_width, set_fixed_height, set_min_height, set_max_height')

        if new_imports:
            for imp in reversed(new_imports):
                lines.insert(insert_idx, imp)

    return '\n'.join(lines)


def refactor_file(filepath: Path) -> dict:
    """Refactor a single file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content

        # Apply all patterns
        for pattern, replacement in PATTERNS.items():
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Add imports if needed
        if content != original:
            content = add_imports(content, filepath)

        # Write back
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return {'file': str(filepath.relative_to(PROJECT_ROOT)), 'modified': True}

        return {'file': str(filepath.relative_to(PROJECT_ROOT)), 'modified': False}
    except Exception as e:
        return {'file': str(filepath.relative_to(PROJECT_ROOT)), 'error': str(e)}


def main():
    """Run bulk refactoring."""
    files = list(SRC_ROOT.rglob('*.py'))

    # Skip __init__.py and already themed files
    files_to_process = [
        f for f in files
        if f.name != '__init__.py'
        and 'theme' not in str(f)
    ]

    print(f"Processing {len(files_to_process)} files...")

    results = {'modified': 0, 'errors': 0, 'skipped': 0}

    for filepath in files_to_process:
        result = refactor_file(filepath)
        if result.get('error'):
            results['errors'] += 1
            print(f"ERROR: {result['file']}: {result['error']}")
        elif result.get('modified'):
            results['modified'] += 1
            print(f"[OK] {result['file']}")
        else:
            results['skipped'] += 1

    print(f"\nResults:")
    print(f"  Modified: {results['modified']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")


if __name__ == '__main__':
    main()
