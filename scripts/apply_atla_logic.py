import json
import uuid

WORKFLOW_FILE = "Projects/MonthlyMuhasebe/scenarios/ck_bogazici_login_updated.json"


def apply_changes():
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", {})
    connections = data.get("connections", [])

    # 1. Add 'check_atla' node (Run Script)
    check_atla_id = "check_atla"
    nodes[check_atla_id] = {
        "node_id": check_atla_id,
        "node_type": "BrowserRunScriptNode",
        "name": "Check Atla Visible",
        "position": [4800, -350],  # Position it around wait_for_atla
        "config": {
            "script": """
selector = "button:has-text('Atla'), a:has-text('Atla'), *:has-text('Atla')"
is_visible = False
if 'page' in locals() and page:
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            if await el.is_visible(timeout=3000):
                is_visible = True
    except Exception as e:
        logger.warning(f"Check Atla failed: {e}")
return is_visible
""",
            "timeout": "10000",
        },
    }

    # 2. Add 'if_atla' node
    if_atla_id = "if_atla"
    nodes[if_atla_id] = {
        "node_id": if_atla_id,
        "node_type": "IfNode",
        "name": "If Atla Visible",
        "position": [5000, -350],
        "config": {"expression": "{{check_atla.result}}"},
    }

    # 3. Modify Connections

    # Remove existing: wait_for_atla -> click_atla (exec)
    connections = [
        c
        for c in connections
        if not (
            (c["source_node"] == "wait_for_atla" and c["target_node"] == "click_atla")
            or (
                c["source_node"] == "click_login"
                and c["target_node"] == "click_atla"
                and c["source_port"] == "page"
            )
        )
    ]

    # Add new connections
    new_connections = [
        # wait_for_atla -> check_atla
        {
            "source_node": "wait_for_atla",
            "source_port": "exec_out",
            "target_node": check_atla_id,
            "target_port": "exec_in",
        },
        # click_login (page) -> check_atla (page)
        {
            "source_node": "click_login",
            "source_port": "page",
            "target_node": check_atla_id,
            "target_port": "page",
        },
        # check_atla -> if_atla
        {
            "source_node": check_atla_id,
            "source_port": "exec_out",
            "target_node": if_atla_id,
            "target_port": "exec_in",
        },
        # if_atla (true) -> click_atla
        {
            "source_node": if_atla_id,
            "source_port": "true",
            "target_node": "click_atla",
            "target_port": "exec_in",
        },
        # if_atla (false) -> nav_fatura
        {
            "source_node": if_atla_id,
            "source_port": "false",
            "target_node": "nav_fatura",
            "target_port": "exec_in",
        },
        # check_atla (page) -> click_atla (page) (chaining)
        {
            "source_node": check_atla_id,
            "source_port": "page",
            "target_node": "click_atla",
            "target_port": "page",
        },
    ]

    connections.extend(new_connections)

    # Save
    data["nodes"] = nodes
    data["connections"] = connections

    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Successfully applied Atla logic changes.")


if __name__ == "__main__":
    apply_changes()
