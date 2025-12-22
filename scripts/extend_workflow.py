import orjson
from pathlib import Path

path = Path("Projects/MonthlyMuhasebe/scenarios/ck_bogazici_login_updated.json")
data = orjson.loads(path.read_bytes())

# New nodes for the post-login flow
new_nodes = {
    "nav_fatura": {
        "node_id": "nav_fatura",
        "node_type": "ClickElementNode",
        "name": "Click Fatura Bilgileri",
        "position": [3600, 100],
        "config": {
            "selector": "a.m-menu__link[href='/Fatura/Odeme'], text='FATURA BİLGİLERİ'",
            "timeout": "10000",
            "wait_for_visible": True,
        },
    },
    "select_account": {
        "node_id": "select_account",
        "node_type": "SelectDropdownNode",
        "name": "Select Account 4007119742",
        "position": [3800, 100],
        "config": {
            "selector": "select#hesapddl",
            "select_by": "value",
            "value": "4007119742",
            "timeout": "10000",
        },
    },
    "click_view_bill": {
        "node_id": "click_view_bill",
        "node_type": "ClickElementNode",
        "name": "Click Faturamı Görüntüle",
        "position": [4000, 100],
        "config": {
            "selector": "a.btn:has-text('Faturamı Görüntüle')",
            "timeout": "10000",
            "wait_for_visible": True,
        },
    },
    "save_invoice_pdf": {
        "node_id": "save_invoice_pdf",
        "node_type": "BrowserRunScriptNode",
        "name": "Save Invoice PDF",
        "position": [4200, 100],
        "config": {
            "script": """
import os
import asyncio
from datetime import datetime

# Path configuration
dest_dir = r"C:\\Users\\Rau\\Desktop\\muhasebe"
os.makedirs(dest_dir, exist_ok=True)

# Filename based on project name and timestamp/account
project_name = "MonthlyMuhasebe"
account_num = "4007119742"
filename = f"{project_name}_Fatura_{account_num}_{datetime.now().strftime('%Y%m%d')}.pdf"
full_path = os.path.join(dest_dir, filename)

logger.info(f"Targeting PDF save to: {full_path}")

# Wait for PDF viewer/modal
logger.info("Waiting for PDF modal/viewer...")
await asyncio.sleep(2)

# Handle potential 'Lütfen Bekleyiniz' overlay
try:
    overlay_selector = ".blockUI.blockOverlay, #wait-overlay" # Common patterns
    for _ in range(20): # Max 10 seconds
        overlay = await page.query_selector(overlay_selector)
        if not overlay or not await overlay.is_visible():
            break
        logger.info("Waiting for overlay to disappear...")
        await asyncio.sleep(0.5)
except:
    pass

# Try to find the iframe with PDF
iframe = None
for frame in page.frames:
    if "pdf" in frame.url.lower() or "blob:" in frame.url.lower() or "/shared/pdf" in frame.url.lower():
        iframe = frame
        break

if iframe:
    logger.info(f"Found PDF iframe: {iframe.url}, attempting capture...")
    try:
        # Some viewers are blobs, we use page.pdf on the main page which includes the modal
        # If the user specifically wants to PRINT, page.pdf() is exactly that.
        await page.pdf(path=full_path, format="A4", print_background=True)
    except Exception as e:
        logger.error(f"Iframe print failed: {e}. Trying full page.")
        await page.pdf(path=full_path, format="A4", print_background=True)
else:
    logger.warning("PDF iframe not found, attempting full page capture...")
    await page.pdf(path=full_path, format="A4", print_background=True)

logger.info(f"Successfully saved PDF to {full_path}")
result = full_path
"""
        },
    },
    "verify_file": {
        "node_id": "verify_file",
        "node_type": "FileSystemSuperNode",
        "name": "Verify Invoice Path",
        "position": [4400, 100],
        "config": {"action": "File Exists", "path": "C:\\Users\\Rau\\Desktop\\muhasebe"},
    },
}

# Add new nodes to data
data["nodes"].update(new_nodes)

# Connect them
# check_final_success (true) -> nav_fatura
new_connections = [
    {
        "source_node": "check_final_success",
        "source_port": "true",
        "target_node": "nav_fatura",
        "target_port": "exec_in",
    },
    {
        "source_node": "check_final_success",
        "source_port": "page",
        "target_node": "nav_fatura",
        "target_port": "page",
    },
    {
        "source_node": "nav_fatura",
        "source_port": "exec_out",
        "target_node": "select_account",
        "target_port": "exec_in",
    },
    {
        "source_node": "nav_fatura",
        "source_port": "page",
        "target_node": "select_account",
        "target_port": "page",
    },
    {
        "source_node": "select_account",
        "source_port": "exec_out",
        "target_node": "click_view_bill",
        "target_port": "exec_in",
    },
    {
        "source_node": "select_account",
        "source_port": "page",
        "target_node": "click_view_bill",
        "target_port": "page",
    },
    {
        "source_node": "click_view_bill",
        "source_port": "exec_out",
        "target_node": "save_invoice_pdf",
        "target_port": "exec_in",
    },
    {
        "source_node": "click_view_bill",
        "source_port": "page",
        "target_node": "save_invoice_pdf",
        "target_port": "page",
    },
    {
        "source_node": "save_invoice_pdf",
        "source_port": "exec_out",
        "target_node": "verify_file",
        "target_port": "exec_in",
    },
]

data["connections"].extend(new_connections)

# Save result
path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
print("✅ Workflow extended with Fatura Bilgileri flow")
