import sys

sys.path.insert(0, "src")

import traceback

try:
    from casare_rpa.presentation.canvas.theme_system.design_tokens import TOKENS

    print("OK:", TOKENS.spacing.md)
except Exception as e:
    traceback.print_exc()
