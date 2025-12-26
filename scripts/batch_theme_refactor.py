"""
Batch Theme Refactor Script for CasareRPA.

This script performs bulk replacements of hardcoded UI values with theme tokens.
Usage: python scripts/batch_theme_refactor.py
"""

from pathlib import Path
import re

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CANVAS_ROOT = PROJECT_ROOT / "src" / "casare_rpa" / "presentation" / "canvas"


# Replacement patterns: (pattern, replacement, needs_import_check)
REPLACEMENTS = [
    # setFixedSize -> set_fixed_size
    (r'\.setFixedSize\((\d+),\s*(\d+)\)', r'set_fixed_size(widget, \1, \2)', 'set_fixed_size'),

    # setMinimumSize -> set_min_size
    (r'\.setMinimumSize\((\d+),\s*(\d+)\)', r'set_min_size(widget, \1, \2)', 'set_min_size'),
    (r'\.setMinimumSize\((\d+)\)', r'set_min_width(widget, \1)', 'set_min_width'),

    # setMaximumSize -> set_max_size
    (r'\.setMaximumSize\((\d+),\s*(\d+)\)', r'set_max_size(widget, \1, \2)', 'set_max_size'),
    (r'\.setMaximumSize\((\d+)\)', r'set_max_width(widget, \1)', 'set_max_width'),

    # setFixedWidth -> set_fixed_width
    (r'\.setFixedWidth\((\d+)\)', r'set_fixed_width(widget, \1)', 'set_fixed_width'),

    # setFixedHeight -> set_fixed_height
    (r'\.setFixedHeight\((\d+)\)', r'set_fixed_height(widget, \1)', 'set_fixed_height'),

    # setMinimumWidth -> set_min_width
    (r'\.setMinimumWidth\((\d+)\)', r'set_min_width(widget, \1)', 'set_min_width'),

    # setMaximumWidth -> set_max_width
    (r'\.setMaximumWidth\((\d+)\)', r'set_max_width(widget, \1)', 'set_max_width'),

    # setContentsMargins with 4 args
    (r'\.setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)',
     r'set_margins(layout, (\1, \2, \3, \4))', 'set_margins'),

    # setSpacing
    (r'\.setSpacing\((\d+)\)', r'set_spacing(layout, \1)', 'set_spacing'),

    # resize() calls
    (r'\.resize\((\d+),\s*(\d+)\)', r'set_fixed_size(widget, \1, \2)', 'set_fixed_size'),

    # Common hardcoded size replacements in stylesheets
    (r'border-radius:\s*(\d+)px', r'border-radius: {TOKENS.radii.sm}px', 'TOKENS'),
    (r'padding:\s*(\d+)px', r'padding: {TOKENS.spacing.md}px', 'TOKENS'),
    (r'font-size:\s*(\d+)px', r'font-size: {TOKENS.fonts.size_md}px', 'TOKENS'),

    # Dialog size constants
    (r'\(400,\s*500\)', r'(TOKENS.sizes.dialog_width_sm, TOKENS.sizes.dialog_height_md)', 'TOKENS'),
    (r'\(600,\s*500\)', r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)', 'TOKENS'),
    (r'\(800,\s*600\)', r'(TOKENS.sizes.dialog_width_lg, TOKENS.sizes.dialog_height_lg)', 'TOKENS'),
]


def refactor_file(filepath: Path) -> dict:
    """Refactor a single file. Returns changes made."""
    content = filepath.read_text(encoding='utf-8')
    original = content

    changes = []
    helpers_needed = set()
    tokens_needed = False

    for pattern, replacement, import_check in REPLACEMENTS:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            if import_check == 'TOKENS':
                tokens_needed = True
            else:
                helpers_needed.add(import_check)
            changes.append(f"{import_check}: {len(matches)} matches")

    if content != original:
        # Check/add imports
        lines = content.split('\n')
        import_idx = -1
        for i, line in enumerate(lines):
            if 'from casare_rpa.presentation.canvas.theme_system' in line:
                import_idx = i
                break
            if 'from PySide6' in line:
                import_idx = i - 1
                break

        if import_idx >= 0:
            # Add needed imports
            new_imports = []
            if helpers_needed:
                helpers_str = ', '.join(f'"{h}"' for h in sorted(helpers_needed))
                new_imports.append(f'from casare_rpa.presentation.canvas.theme_system.helpers import {", ".join(sorted(helpers_needed))}')
            if tokens_needed:
                new_imports.append('from casare_rpa.presentation.canvas.theme_system import TOKENS')

            # Check what's already imported
            existing_imports = set()
            for line in lines[import_idx:]:
                if 'from casare_rpa.presentation.canvas.theme_system' in line:
                    if 'helpers' in line:
                        existing_imports.update(line.split('import')[1].split())
                    if 'TOKENS' in line:
                        tokens_needed = False
                        existing_imports.add('TOKENS')
                elif line.startswith('from ') or line.startswith('import '):
                    break

            # Insert new imports
            insert_pos = import_idx
            for imp in reversed(new_imports):
                if 'TOKENS' in imp and 'TOKENS' in existing_imports:
                    continue
                if 'helpers' in imp:
                    already_imported = any(h in line for line in lines for h in helpers_needed)
                    if already_imported:
                        continue
                lines.insert(insert_pos, imp)

        filepath.write_text('\n'.join(lines), encoding='utf-8')

    return {
        'file': str(filepath.relative_to(PROJECT_ROOT)),
        'changes': changes,
        'modified': content != original
    }


def main():
    """Run batch refactoring on all Python files in canvas."""
    files = list(CANVAS_ROOT.rglob('*.py'))

    # Filter out already refactored files (those using theme_system imports)
    needs_refactor = []
    for f in files:
        content = f.read_text(encoding='utf-8')
        if 'theme_system' not in content and any(p.search(content) for p in [re.compile(r'setFixedSize\('), re.compile(r'setContentsMargins\(')]):
            needs_refactor.append(f)

    print(f"Found {len(needs_refactor)} files needing refactoring")

    results = []
    for f in needs_refactor:
        try:
            result = refactor_file(f)
            if result['modified']:
                results.append(result)
                print(f"✓ {result['file']}: {', '.join(result['changes'])}")
        except Exception as e:
            print(f"✗ {f}: {e}")

    print(f"\nRefactored {len(results)} files")


if __name__ == '__main__':
    main()
