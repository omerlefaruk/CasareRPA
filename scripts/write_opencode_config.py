import json
from pathlib import Path

cfg_dir = Path.home() / ".config" / "opencode"
cfg_dir.mkdir(parents=True, exist_ok=True)
cfg = {
    "$schema": "https://opencode.ai/config.json",
    "plugin": [
        "file:///C:/Users/Rau/Desktop/CasareRPA/external_plugins/opencode-gemini-auth"
    ],
}
(cfg_dir / "opencode.json").write_text(json.dumps(cfg, indent=2))
print("wrote", cfg_dir / "opencode.json")
