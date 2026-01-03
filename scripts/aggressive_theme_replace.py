"""
Aggressive Bulk Theme Replace - Direct Edit
"""
import re
from pathlib import Path

SRC = Path("src/casare_rpa/presentation/canvas")

# Files to target
TARGET_FILES = [
    "selectors/selector_dialog.py",
    "selectors/element_selector_dialog.py",
    "selectors/desktop_selector_builder.py",
    "selectors/unified_selector_dialog.py",
    "selectors/state/selector_state.py",
    "selectors/components/selector_preview.py",
    "selectors/widgets/picker_toolbar.py",
    "selectors/widgets/element_preview_widget.py",
    "selectors/widgets/anchor_widget.py",
    "ui/base_widget.py",
    "ui/dialogs/login_dialog.py",
    "ui/dialogs/project_wizard.py",
    "ui/dialogs/gemini_studio_oauth_dialog.py",
    "ui/dialogs/update_dialog.py",
    "ui/dialogs/recording_review_dialog.py",
    "ui/panels/panel_ux_helpers.py",
    "ui/panels/port_legend_panel.py",
    "ui/panels/history_tab.py",
    "ui/panels/debug_console_panel.py",
    "ui/panels/log_tab.py",
    "ui/widgets/context_menu.py",
    "ui/widgets/collapsible_section.py",
    "ui/widgets/cascading_dropdown.py",
    "ui/widgets/anchor_selector_widget.py",
    "ui/widgets/ai_settings_widget.py",
    "ui/widgets/zoom_widget.py",
    "ui/toolbars/recording_toolbar.py",
    "ui/toolbars/debug_toolbar.py",
    "ui/toolbars/alignment_toolbar.py",
    "ui/toolbars/main_toolbar.py",
    "ui/property_panel/property_renderer.py",
    "components/toolbar_builder.py",
    "components/status_bar_manager.py",
    "connections/connection_cutter.py",
    "connections/node_insert.py",
    "connections/wire_bundler.py",
    "connections/smart_routing.py",
    "controllers/execution_controller.py",
    "controllers/menu_controller.py",
    "controllers/node_controller.py",
    "controllers/panel_controller.py",
    "controllers/viewport_controller.py",
    "search/node_search.py",
    "search/command_palette.py",
]

# Key replacements
REPLACEMENTS = [
    # Method calls with actual widget/layout context
    (r'self\.setFixedSize\((\d+),\s*(\d+)\)', r'set_fixed_size(self, \1, \2)'),
    (r'self\.setMinimumSize\((\d+),\s*(\d+)\)', r'set_min_size(self, \1, \2)'),
    (r'self\.setMaximumSize\((\d+),\s*(\d+)\)', r'set_max_size(self, \1, \2)'),
    (r'self\.setMinimumWidth\((\d+)\)', r'set_min_width(self, \1)'),
    (r'self\.setMaximumWidth\((\d+)\)', r'set_max_width(self, \1)'),
    (r'self\.setFixedWidth\((\d+)\)', r'set_fixed_width(self, \1)'),
    (r'self\.setFixedHeight\((\d+)\)', r'set_fixed_height(self, \1)'),

    (r'(\w+)\.setFixedSize\((\d+),\s*(\d+)\)', r'set_fixed_size(\1, \2, \3)'),
    (r'(\w+)\.setMinimumSize\((\d+),\s*(\d+)\)', r'set_min_size(\1, \2, \3)'),
    (r'(\w+)\.setMaximumSize\((\d+),\s*(\d+)\)', r'set_max_size(\1, \2, \3)'),
    (r'(\w+)\.setMinimumWidth\((\d+)\)', r'set_min_width(\1, \2)'),
    (r'(\w+)\.setMaximumWidth\((\d+)\)', r'set_max_width(\1, \2)'),
    (r'(\w+)\.setFixedWidth\((\d+)\)', r'set_fixed_width(\1, \2)'),

    (r'(\w+)\.setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', r'set_margins(\1, (\2, \3, \4, \5))'),
    (r'layout\.setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', r'set_margins(layout, (\1, \2, \3, \4))'),
    (r'(\w+)\.setSpacing\((\d+)\)', r'set_spacing(\1, \2)'),
    (r'layout\.setSpacing\((\d+)\)', r'set_spacing(layout, \1)'),

    # Common sizes
    (r'\(200,\s*200\)', r'(TOKENS.sizes.panel_width_min, TOKENS.sizes.panel_width_min)'),
    (r'\(250,\s*250\)', r'(TOKENS.sizes.panel_width_default, TOKENS.sizes.panel_width_default)'),
    (r'\(300,\s*200\)', r'(TOKENS.sizes.panel_width_default, TOKENS.sizes.panel_width_min)'),
    (r'\(300,\s*300\)', r'(TOKENS.sizes.panel_width_default, TOKENS.sizes.panel_width_default)'),
    (r'\(400,\s*300\)', r'(TOKENS.sizes.dialog_width_sm, TOKENS.sizes.dialog_height_sm)'),
    (r'\(400,\s*400\)', r'(TOKENS.sizes.dialog_width_sm, TOKENS.sizes.dialog_width_sm)'),
    (r'\(500,\s*300\)', r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_sm)'),
    (r'\(500,\s*400\)', r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)'),
    (r'\(600,\s*400\)', r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)'),
    (r'\(600,\s*500\)', r'(TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_md)'),
    (r'\(800,\s*600\)', r'(TOKENS.sizes.dialog_width_lg, TOKENS.sizes.dialog_height_lg)'),
    (r'\(800,\s*500\)', r'(TOKENS.sizes.dialog_width_lg, TOKENS.sizes.dialog_height_md)'),
    (r'\(1000,\s*600\)', r'(TOKENS.sizes.dialog_width_xl, TOKENS.sizes.dialog_height_lg)'),

    # Individual size values
    (r'\b200\b', r'TOKENS.sizes.panel_width_min'),
    (r'\b250\b', r'TOKENS.sizes.panel_width_default'),
    (r'\b300\b', r'TOKENS.sizes.panel_width_default'),
    (r'\b400\b', r'TOKENS.sizes.dialog_width_sm'),
    (r'\b500\b', r'TOKENS.sizes.dialog_width_md'),
    (r'\b600\b', r'TOKENS.sizes.dialog_width_lg'),
    (r'\b800\b', r'TOKENS.sizes.dialog_width_lg'),

    # Spacing in stylesheets
    (r'padding:\s*4px', r'padding: {TOKENS.spacing.sm}px'),
    (r'padding:\s*6px', r'padding: {TOKENS.spacing.sm}px'),
    (r'padding:\s*8px', r'padding: {TOKENS.spacing.md}px'),
    (r'padding:\s*10px', r'padding: {TOKENS.spacing.md}px'),
    (r'padding:\s*12px', r'padding: {TOKENS.spacing.lg}px'),
    (r'padding:\s*16px', r'padding: {TOKENS.spacing.xl}px'),
    (r"padding:\s*'4px'", r"padding: f'{TOKENS.spacing.sm}px'"),
    (r"padding:\s*'8px'", r"padding: f'{TOKENS.spacing.md}px'"),
    (r"padding:\s*'12px'", r"padding: f'{TOKENS.spacing.lg}px'"),
    (r'padding:\s*f"4px"', r'padding: f"{TOKENS.spacing.sm}px"'),
    (r'padding:\s*f"8px"', r'padding: f"{TOKENS.spacing.md}px"'),
    (r'padding:\s*f"12px"', r'padding: f"{TOKENS.spacing.lg}px"'),

    (r'margin:\s*4px', r'margin: {TOKENS.spacing.sm}px'),
    (r'margin:\s*8px', r'margin: {TOKENS.spacing.md}px'),
    (r'margin:\s*12px', r'margin: {TOKENS.spacing.lg}px'),
    (r'margin:\s*16px', r'margin: {TOKENS.spacing.xl}px'),

    (r'border-radius:\s*2px', r'border-radius: {TOKENS.radii.xs}px'),
    (r'border-radius:\s*3px', r'border-radius: {TOKENS.radii.xs}px'),
    (r'border-radius:\s*4px', r'border-radius: {TOKENS.radii.sm}px'),
    (r'border-radius:\s*5px', r'border-radius: {TOKENS.radii.md}px'),
    (r'border-radius:\s*6px', r'border-radius: {TOKENS.radii.md}px'),
    (r'border-radius:\s*8px', r'border-radius: {TOKENS.radii.md}px'),
    (r'border-radius:\s*10px', r'border-radius: {TOKENS.radii.lg}px'),

    (r"font-size:\s*10px", r"font-size: {TOKENS.fonts.xs}px"),
    (r"font-size:\s*11px", r"font-size: {TOKENS.fonts.sm}px"),
    (r"font-size:\s*12px", r"font-size: {TOKENS.fonts.md}px"),
    (r"font-size:\s*13px", r"font-size: {TOKENS.fonts.md}px"),
    (r"font-size:\s*14px", r"font-size: {TOKENS.fonts.lg}px"),
    (r"font-size:\s*16px", r"font-size: {TOKENS.fonts.xl}px"),
    (r"font-size:\s*18px", r"font-size: {TOKENS.fonts.xl}px"),
    (r"font-size:\s*20px", r"font-size: {TOKENS.fonts.xxl}px"),

    # Width/Height in stylesheets
    (r'min-width:\s*80px', r'min-width: {TOKENS.sizes.button_min_width}px'),
    (r'min-width:\s*100px', r'min-width: {TOKENS.sizes.button_width_sm}px'),
    (r'min-width:\s*150px', r'min-width: {TOKENS.sizes.combo_width_md}px'),
    (r'min-width:\s*200px', r'min-width: {TOKENS.sizes.panel_width_min}px'),
    (r'min-width:\s*250px', r'min-width: {TOKENS.sizes.panel_width_default}px'),
    (r'min-width:\s*300px', r'min-width: {TOKENS.sizes.panel_width_default}px'),
    (r'min-height:\s*24px', r'min-height: {TOKENS.sizes.input_height_sm}px'),
    (r'min-height:\s*28px', r'min-height: {TOKENS.sizes.input_height_md}px'),
    (r'min-height:\s*32px', r'min-height: {TOKENS.sizes.button_height_lg}px'),
    (r'max-width:\s*200px', r'max-width: {TOKENS.sizes.panel_width_min}px'),
    (r'max-width:\s*250px', r'max-width: {TOKENS.sizes.combo_width_md}px'),
    (r'max-width:\s*300px', r'max-width: {TOKENS.sizes.panel_width_default}px'),
    (r'max-width:\s*400px', r'max-width: {TOKENS.sizes.panel_width_max}px'),
    (r'width:\s*200px', r'width: {TOKENS.sizes.panel_width_min}px'),
    (r'width:\s*250px', r'width: {TOKENS.sizes.panel_width_default}px'),
    (r'height:\s*24px', r'height: {TOKENS.sizes.input_height_sm}px'),
    (r'height:\s*28px', r'height: {TOKENS.sizes.input_height_md}px'),
    (r'height:\s*32px', r'height: {TOKENS.sizes.button_height_lg}px'),

    # Colors (hex)
    (r'#1e1e1e', r'{THEME.bg_darkest}'),
    (r'#252526', r'{THEME.bg_dark}'),
    (r'#2d2d30', r'{THEME.bg_medium}'),
    (r'#3c3c3c', r'{THEME.bg_light}'),
    (r'#f0f0f0', r'{THEME.bg_lightest}'),
    (r'#cccccc', r'{THEME.text_muted}'),
    (r'#aaaaaa', r'{THEME.text_disabled}'),
    (r'#e0e0e0', r'{THEME.text_secondary}'),
    (r'#ffffff(?=[\'"\s])', r'{THEME.text_primary}'),
    (r'#3e3e42', r'{THEME.border}'),
    (r'#454545', r'{THEME.border}'),
    (r'#007acc', r'{THEME.accent_primary}'),
    (r'#0078d4', r'{THEME.accent_primary}'),
    (r'#4caf50', r'{THEME.status_success}'),
    (r'#ff9800', r'{THEME.status_warning}'),
    (r'#ff5722', r'{THEME.status_error}'),
    (r'#2196f3', r'{THEME.status_info}'),
]


def ensure_imports(content):
    lines = content.split('\n')

    # Check existing imports
    has_tokens = any('TOKENS' in line for line in lines[:50])
    has_helpers = any('theme.helpers' in line for line in lines[:50])
    has_theme = any('THEME' in line and 'import' in line for line in lines[:50])

    # Find insertion point
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith(('from ', 'import ')):
            insert_idx = i + 1
        elif line.startswith(('class ', 'def ')):
            break

    new_imports = []
    if '{TOKENS' in content and not has_tokens:
        new_imports.append('from casare_rpa.presentation.canvas.theme import TOKENS')
    if any(h in content for h in ['set_fixed_size', 'set_min_size', 'set_margins', 'set_spacing']) and not has_helpers:
        new_imports.append('from casare_rpa.presentation.canvas.theme.helpers import set_fixed_size, set_min_size, set_max_size, set_margins, set_spacing, set_min_width, set_max_width, set_fixed_width, set_fixed_height')
    if '{THEME' in content and not has_theme:
        new_imports.append('from casare_rpa.presentation.canvas.theme import THEME')

    if new_imports:
        for imp in reversed(new_imports):
            lines.insert(insert_idx, imp)

    return '\n'.join(lines)


def process_file(filepath):
    try:
        text = filepath.read_text(encoding='utf-8')
        original = text

        for pattern, repl in REPLACEMENTS:
            text = re.sub(pattern, repl, text, flags=re.MULTILINE | re.IGNORECASE)

        if text != original:
            text = ensure_imports(text)
            filepath.write_text(text, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"ERROR {filepath}: {e}")
        return False


def main():
    modified = 0
    for rel_path in TARGET_FILES:
        filepath = SRC / rel_path
        if filepath.exists():
            if process_file(filepath):
                print(f"[OK] {rel_path}")
                modified += 1
            else:
                print(f"[SKIP] {rel_path}")
        else:
            print(f"[NOT FOUND] {rel_path}")

    print(f"\nModified: {modified}/{len(TARGET_FILES)}")


if __name__ == '__main__':
    main()

