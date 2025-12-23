import json
import os
from pathlib import Path
from typing import Dict


def _require_secret(var_name: str) -> str:
    """Fetch a secret from the environment, raising if it is missing."""
    try:
        value = os.environ[var_name]
    except KeyError as exc:
        raise RuntimeError(f"Missing required environment variable: {var_name}") from exc
    if not value.strip():
        raise RuntimeError(f"Environment variable {var_name} cannot be empty")
    return value


def _build_mcp_servers() -> dict[str, dict[str, object]]:
    return {
        "exa": {
            "type": "local",
            "command": ["npx", "-y", "exa-mcp-server"],
            "environment": {"EXA_API_KEY": _require_secret("EXA_API_KEY")},
        },
        "context7": {
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@upstash/context7-mcp@latest",
            ],
            "environment": {"CONTEXT7_API_KEY": _require_secret("CONTEXT7_API_KEY")},
        },
        "ref": {
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@upstash/context7-mcp@latest",
            ],
            "environment": {"CONTEXT7_API_KEY": _require_secret("CONTEXT7_API_KEY")},
        },
        "codebase": {
            "type": "local",
            "command": [
                "python",
                str((Path(__file__).parent.parent / "scripts" / "chroma_search_mcp.py").resolve()),
            ],
            "environment": {},
        },
        "filesystem": {
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str((Path(__file__).parent.parent).resolve()),
            ],
            "environment": {},
        },
        "git": {
            "type": "local",
            "command": [
                "python",
                "-m",
                "mcp_server_git",
                "--repository",
                str((Path(__file__).parent.parent).resolve()),
            ],
            "environment": {},
        },
        "sequential-thinking": {
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@modelcontextprotocol/server-sequential-thinking",
            ],
            "environment": {},
        },
        "playwright": {
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@playwright/mcp@latest",
            ],
            "environment": {},
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
