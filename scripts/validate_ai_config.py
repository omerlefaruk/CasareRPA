import json
import re
import sys
from pathlib import Path

# Add src to sys.path to import gemini_config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from casare_rpa.infrastructure.ai.gemini_config import (
    AgentCapability,
    GeminiConfig,
    GeminiParams,
    SkillDefinition,
)


def parse_markdown_table(content: str, table_header: str) -> list[dict[str, str]]:
    """Simple parser for markdown tables."""
    lines = content.split("\n")
    start_index = -1
    for i, line in enumerate(lines):
        if table_header in line:
            start_index = i + 2  # Skip header and separator
            break

    if start_index == -1:
        return []

    items = []
    for line in lines[start_index:]:
        if not line.strip() or not line.startswith("|"):
            break
        cols = [c.strip() for c in line.split("|") if c.strip()]
        items.append(cols)
    return items


def parse_markdown_list(content: str, header: str) -> list[str]:
    """Simple parser for markdown lists."""
    lines = content.split("\n")
    start_index = -1
    for i, line in enumerate(lines):
        if header in line:
            start_index = i + 1
            break

    if start_index == -1:
        return []

    items = []
    for line in lines[start_index:]:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            break
        if line.startswith("-"):
            # Extract filename from - `filename.md` - description
            match = re.search(r"- `([^`]+)`", line)
            if match:
                items.append(match.group(1))
    return items


def load_config():
    root = Path(__file__).parent.parent

    # 1. Load Gemini Params from GEMINI.md
    gemini_md = (root / "GEMINI.md").read_text(encoding="utf-8")
    agents_md = (root / "AGENTS.md").read_text(encoding="utf-8")

    # Extraction using regex for simplicity in this script
    model_match = re.search(r"- \*\*Model:\*\* `([^`]+)`", gemini_md)
    temp_match = re.search(r"- \*\*Temperature:\*\* ([0-9.]+)", gemini_md)

    params = GeminiParams(
        model=model_match.group(1) if model_match else "gemini-2.0-flash-exp",
        temperature=float(temp_match.group(1)) if temp_match else 0.0,
    )

    # 2. Load Agents from AGENTS.md / GEMINI.md
    agent_items = parse_markdown_table(gemini_md, "## Agent Capabilities")
    agents = []
    for item in agent_items:
        if len(item) >= 3:
            name, desc, skills_str = (
                item[0].replace("`", ""),
                item[1],
                item[2].replace("`", ""),
            )
            skills = [s.strip().replace("`", "") for s in skills_str.split(",")]
            agents.append(AgentCapability(name=name, description=desc, skills=skills))

    # 3. Load Skills from GEMINI.md
    skill_items = parse_markdown_table(gemini_md, "## Skill Mappings")
    skills = []

    # Get concrete schemas from GEMINI.md
    for item in skill_items:
        if len(item) >= 3:
            name, desc, _schema_name = (
                item[0].replace("`", ""),
                item[1],
                item[2].replace("`", ""),
            )

            # Find the schema in the file
            schema_pattern = rf"#### {name}\n```json\n(.*?)\n```"
            schema_match = re.search(schema_pattern, gemini_md, re.DOTALL)
            schema_def = json.loads(schema_match.group(1)) if schema_match else {}

            skills.append(SkillDefinition(name=name, description=desc, schema_def=schema_def))

    # 4. Cross-validate with AGENTS.md
    agents_skills = parse_markdown_list(agents_md, "## Skills Reference")
    defined_skill_names = {s.name for s in skills}
    for skill_file in agents_skills:
        skill_name = skill_file.replace(".md", "").strip()
        if skill_name not in defined_skill_names:
            print(
                f"⚠️ Warning: Skill '{skill_name}' mentioned in AGENTS.md but not defined in GEMINI.md"
            )

    config = GeminiConfig(params=params, agents=agents, skills=skills)
    return config


def main():
    print("Validating AI Configuration...")
    try:
        config = load_config()
        print("✅ Configuration loaded and validated successfully.")

        # Save to machine-readable JSON
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)

        output_path = config_dir / "ai_agent_config.json"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))

        print(f"✅ Unified configuration saved to {output_path}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
