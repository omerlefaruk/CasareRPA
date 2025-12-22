#!/usr/bin/env python
"""
CasareRPA Unified Management Script.

Usage:
    python manage.py --help
    python manage.py canvas
    python manage.py robot start
    python manage.py orchestrator start
    python manage.py dashboard
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path to ensure imports work even if not installed as package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from casare_rpa.cli.main import app

if __name__ == "__main__":
    app()
