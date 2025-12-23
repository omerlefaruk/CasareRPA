"""Add CAPTCHA nodes to registry and fix connection."""

from pathlib import Path

import orjson

# Fix registry_data.py
registry_path = Path("src/casare_rpa/nodes/registry_data.py")
content = registry_path.read_text(encoding="utf-8")

# Add CAPTCHA nodes if not present
if "DetectCaptchaNode" not in content:
    # Find insertion point after BrowserRunScriptNode
    insert_after = '"BrowserRunScriptNode": "browser.scripting",'
    insert_text = """
    # Browser CAPTCHA nodes
    "DetectCaptchaNode": "browser.captcha",
    "SolveCaptchaNode": "browser.captcha",
    "SolveCaptchaAINode": "browser.captcha_ai","""

    content = content.replace(insert_after, insert_after + insert_text)
    registry_path.write_text(content, encoding="utf-8")
    print("✅ Added CAPTCHA nodes to registry_data.py")
else:
    print("✓ CAPTCHA nodes already in registry")

# Clear node mapping cache
cache_file = Path.home() / ".casare_rpa" / "cache" / "node_mapping_cache.json"
if cache_file.exists():
    cache_file.unlink()
    print("✅ Cleared node mapping cache")

# Fix workflow - remove invalid connection to if_captcha_detected.value
workflow_path = Path("Projects/MonthlyMuhasebe/scenarios/ck_bogazici_login_updated.json")
d = orjson.loads(workflow_path.read_bytes())

# Remove invalid connection
d["connections"] = [
    c
    for c in d["connections"]
    if not (c["target_node"] == "if_captcha_detected" and c["target_port"] == "value")
]

# Make sure we have detect_captcha output connected to a variable that IfNode can use
# IfNode uses expression config, so we need to set the expression to use the variable
d["nodes"]["if_captcha_detected"]["config"]["expression"] = "{{detect_captcha.captcha_detected}}"

workflow_path.write_bytes(orjson.dumps(d, option=orjson.OPT_INDENT_2))
print("✅ Fixed workflow connections")

print()
print("Please restart the Canvas (Ctrl+Q and then launch again)")
