import json
import os
from pathlib import Path
from typing import Dict


def _require_secret(var_name: str) -> str:
    """Fetch a secret from the environment, raising if it is missing."""
    try:
        value = os.environ[var_name]
    except KeyError as exc:
        raise RuntimeError(
            f"Missing required environment variable: {var_name}"
        ) from exc
    if not value.strip():
        raise RuntimeError(f"Environment variable {var_name} cannot be empty")
    return value


def _build_mcp_servers() -> Dict[str, Dict[str, object]]:
    return {
        "exa": {
            "type": "local",
            "command": ["C:\\nvm4w\\nodejs\\npx.cmd", "-y", "exa-mcp-server"],
            "environment": {"EXA_API_KEY": _require_secret("EXA_API_KEY")},
        },
        "context7": {
            "type": "local",
            "command": [
                "C:\\nvm4w\\nodejs\\npx.cmd",
                "-y",
                "@upstash/context7-mcp@latest",
            ],
            "environment": {"CONTEXT7_API_KEY": _require_secret("CONTEXT7_API_KEY")},
        },
        "qdrant": {
            "type": "local",
            "command": [
                "C:\\Users\\Rau\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\mcp-server-qdrant.exe"
            ],
            "environment": {
                "QDRANT_LOCAL_PATH": "C:/Users/Rau/Desktop/CasareRPA/.qdrant",
                "COLLECTION_NAME": "casare_codebase",
                "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
            },
        },
    }


def main() -> None:
    cfg_dir = Path.home() / ".config" / "opencode"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    cfg = {
        "$schema": "https://opencode.ai/config.json",
        "mcp": _build_mcp_servers(),
    }

    config_path = cfg_dir / "opencode.json"
    config_path.write_text(json.dumps(cfg, indent=2))
    print("wrote", config_path)


if __name__ == "__main__":
    main()
