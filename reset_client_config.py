"""Reset client configuration to use localhost."""

import os
import sys
from pathlib import Path

# Try to use internal modules if possible, otherwise raw manipulation
try:
    import yaml
except ImportError:
    print("PyYAML not installed, performing raw text replacement...")
    yaml = None


def main():
    app_data = os.environ.get("APPDATA")
    if not app_data:
        print("APPDATA not set, checking home...")
        base_dir = Path.home()
    else:
        base_dir = Path(app_data)

    config_dir = base_dir / "CasareRPA"
    config_file = config_dir / "config.yaml"

    print(f"Checking config at: {config_file}")

    if not config_file.exists():
        print("Config file not found. Creating default localhost config...")
        config_dir.mkdir(parents=True, exist_ok=True)
        content = """# CasareRPA Client Configuration
orchestrator:
  url: http://localhost:8000
  api_key: ""
  verify_ssl: true
  reconnect_delay: 1.0
  max_reconnect_delay: 60.0
robot:
  name: Local-Robot
  capabilities:
  - browser
  - desktop
  tags: []
  max_concurrent_jobs: 2
  environment: default
logging:
  level: INFO
  directory: ./logs
  max_size_mb: 50
  retention_days: 30
first_run_complete: true
"""
        config_file.write_text(content, encoding="utf-8")
        print("Created new config.yaml pointing to localhost.")
        return

    # Update existing config
    content = config_file.read_text(encoding="utf-8")

    if "api.casare.net" in content:
        print("Found production URL. Replacing with localhost...")
        new_content = content.replace("https://api.casare.net", "http://localhost:8000")
        new_content = new_content.replace("wss://api.casare.net", "ws://localhost:8000")
        config_file.write_text(new_content, encoding="utf-8")
        print("Updated config.yaml to use localhost.")
    else:
        print("Config does not seem to point to api.casare.net. Verifying...")
        if "localhost" in content:
            print("Config already looks like localhost.")
        else:
            print("Config is using custom URL. Forcing localhost override...")
            # Simple replace of url line if yaml parsing fails
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if line.strip().startswith("url:"):
                    new_lines.append("  url: http://localhost:8000")
                else:
                    new_lines.append(line)
            config_file.write_text("\n".join(new_lines), encoding="utf-8")
            print("Forced localhost URL.")


if __name__ == "__main__":
    main()
