"""
Robot Configuration
"""
import os
import uuid
from pathlib import Path
from loguru import logger

# Robot Identity
ROBOT_ID_FILE = Path.home() / ".casare_rpa" / "robot_id"
ROBOT_NAME = os.getenv("CASARE_ROBOT_NAME", f"Robot-{os.getenv('COMPUTERNAME', 'Unknown')}")

# Supabase Configuration (To be filled by user)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_robot_id() -> str:
    """Get or create a persistent unique ID for this robot."""
    if ROBOT_ID_FILE.exists():
        return ROBOT_ID_FILE.read_text().strip()
    
    # Create new ID
    new_id = str(uuid.uuid4())
    try:
        ROBOT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        ROBOT_ID_FILE.write_text(new_id)
        logger.info(f"Generated new Robot ID: {new_id}")
    except Exception as e:
        logger.error(f"Failed to save Robot ID: {e}")
        return new_id
    
    return new_id
