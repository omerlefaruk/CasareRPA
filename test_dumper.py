import sys
import os
from loguru import logger

# Add src to path
sys.path.append(os.path.abspath("src"))

try:
    from casare_rpa.infrastructure.ai.registry_dumper import dump_node_manifest

    print("Attempting to dump node manifest...")
    manifest = dump_node_manifest()
    print(f"Success! Total nodes: {manifest.total_count}")
except Exception as e:
    logger.error(f"Failed: {e}")
    import traceback

    traceback.print_exc()
