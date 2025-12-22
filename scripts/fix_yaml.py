import os
import glob

base_dir = r"C:\Users\Rau\.opencode\agent"
# Use recursive glob to catch all .md files in all subdirectories (commands, agents, rules, etc.)
md_files = glob.glob(os.path.join(base_dir, "**", "*.md"), recursive=True)

for path in md_files:
    # Skip directories that might match the pattern
    if os.path.isdir(path):
        continue

    with open(path, "r", encoding="utf-8") as f:
        try:
            lines = f.readlines()
        except Exception:
            continue

    modified = False
    for i, line in enumerate(lines):
        # We only care about the frontmatter at the very top
        if i > 10:
            break

        if line.startswith("description:"):
            # Check if there is a colon in the value part (after the first colon)
            parts = line.split("description:", 1)
            if len(parts) > 1 and ":" in parts[1]:
                desc_content = parts[1].strip()
                # If it's not already quoted or if it's badly quoted, fix it
                if not (desc_content.startswith('"') and desc_content.endswith('"')):
                    # Properly escape existing quotes if necessary, but here we just wrap
                    lines[i] = f'description: "{desc_content}"\n'
                    modified = True
                    print(f"  - Quoted description in {os.path.relpath(path, base_dir)}")

    if modified:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

print("Global check of .opencode/agent directory complete.")
