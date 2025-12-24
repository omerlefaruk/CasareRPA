#!/usr/bin/env python
"""Analyze ruff violations and create a markdown report."""
import subprocess
import json
from collections import Counter, defaultdict
from pathlib import Path

result = subprocess.run(
    ['ruff', 'check', 'src/', '--output-format=json'],
    capture_output=True,
    text=True
)

violations = json.loads(result.stdout) if result.stdout else []

lines = []
lines.append("# Ruff Violations Report")
lines.append(f"\n**Total violations: {len(violations)}**\n")

# Count by rule code
rule_counts = Counter(v['code'] for v in violations)
lines.append("## Violations by Rule\n")
lines.append("| Rule | Count | Description |")
lines.append("|------|-------|-------------|")

# Get one description per rule
violations_by_rule = defaultdict(list)
for v in violations:
    violations_by_rule[v['code']].append(v)

for code, count in rule_counts.most_common():
    items = violations_by_rule[code]
    desc = items[0].get('message', 'N/A')[:60] + "..." if len(items[0].get('message', 'N/A')) > 60 else items[0].get('message', 'N/A')
    lines.append(f"| `{code}` | {count} | {desc} |")

# Count by file (top 20)
file_counts = Counter(v['filename'] for v in violations)
lines.append("\n## Top 20 Files with Most Violations\n")
lines.append("| Count | File |")
lines.append("|-------|------|")
for filename, count in file_counts.most_common(20):
    short_name = filename.replace('C:\\Users\\Rau\\Desktop\\CasareRPA\\', '')
    lines.append(f"| {count} | `{short_name}` |")

# Sample locations for each rule
lines.append("\n## Sample Violations by Rule\n")
for code, items in sorted(violations_by_rule.items(), key=lambda x: -len(x[1])):
    lines.append(f"\n### {code} ({len(items)} violations)")
    lines.append(f"\n**Description:** {items[0].get('message', 'N/A')}\n")
    lines.append("**Sample locations:**")
    for item in items[:5]:
        short_name = item['filename'].replace('C:\\Users\\Rau\\Desktop\\CasareRPA\\', '')
        loc = item.get('location', item.get('end_location', {}))
        row = loc.get('row', 'N/A')
        lines.append(f"- `{short_name}:{row}`")

# Check if any are auto-fixable 
fixable = [v for v in violations if v.get('fix') is not None]
lines.append(f"\n## Auto-Fixable Violations: {len(fixable)}\n")
if fixable:
    fixable_rules = Counter(v['code'] for v in fixable)
    lines.append("| Rule | Count |")
    lines.append("|------|-------|")
    for code, count in fixable_rules.most_common():
        lines.append(f"| `{code}` | {count} |")

# Write report
output_path = Path('.brain/ruff_violations_report.md')
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text('\n'.join(lines), encoding='utf-8')
print(f"Report written to {output_path}")
print(f"Total: {len(violations)} violations")
print(f"Rules: {len(rule_counts)}")
print(f"Files: {len(file_counts)}")
