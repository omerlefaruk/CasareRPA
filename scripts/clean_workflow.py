import orjson
from pathlib import Path

path = Path("Projects/MonthlyMuhasebe/scenarios/ck_bogazici_login_updated.json")
data = orjson.loads(path.read_bytes())

# Clean up duplicate connections by keeping unique pairs of (source, target, source_port, target_port)
seen = set()
unique_connections = []
for conn in data["connections"]:
    key = (conn["source_node"], conn["target_node"], conn["source_port"], conn["target_port"])
    if key not in seen:
        unique_connections.append(conn)
        seen.add(key)

data["connections"] = unique_connections

# Save result cleaned
path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
print(f"✅ Workflow cleaned: {len(unique_connections)} unique connections remaining.")
