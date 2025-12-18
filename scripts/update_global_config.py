import json
import os

path = r"C:\Users\Rau\.opencode\config.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 1. Update existing plugin paths (plural to singular)
    if "plugin" in config:
        new_plugins = []
        for p in config["plugin"]:
            new_plugins.append(p.replace("/plugins/", "/plugin/"))

        # 2. Add the Antigravity OAuth plugin if not present
        if "opencode-google-antigravity-auth@latest" not in new_plugins:
            new_plugins.insert(0, "opencode-google-antigravity-auth@latest")

        config["plugin"] = new_plugins

    # 3. Add Google provider if not present
    if "provider" not in config:
        config["provider"] = {}

    if "google" not in config["provider"]:
        config["provider"]["google"] = {
            "options": {
                "reasoningEffort": "medium",
                "reasoningSummary": "auto",
                "textVerbosity": "medium",
                "store": False,
            },
            "models": {
                "gemini-3-pro-low": {
                    "name": "Gemini 3 Pro Low (OAuth)",
                    "limit": {"context": 1000000, "output": 128000},
                    "modalities": {"input": ["text", "image"], "output": ["text"]},
                    "options": {
                        "reasoningEffort": "low",
                        "reasoningSummary": "auto",
                        "textVerbosity": "medium",
                        "store": False,
                    },
                },
                "gemini-3-pro-medium": {
                    "name": "Gemini 3 Pro Medium (OAuth)",
                    "limit": {"context": 1000000, "output": 128000},
                    "modalities": {"input": ["text", "image"], "output": ["text"]},
                    "options": {
                        "reasoningEffort": "medium",
                        "reasoningSummary": "auto",
                        "textVerbosity": "medium",
                        "store": False,
                    },
                },
                "gemini-3-pro-high": {
                    "name": "Gemini 3 Pro High (OAuth)",
                    "limit": {"context": 1000000, "output": 128000},
                    "modalities": {"input": ["text", "image"], "output": ["text"]},
                    "options": {
                        "reasoningEffort": "high",
                        "reasoningSummary": "detailed",
                        "textVerbosity": "medium",
                        "store": False,
                    },
                },
            },
        }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print("Successfully updated global config.json")
else:
    print(f"Global config not found: {path}")
