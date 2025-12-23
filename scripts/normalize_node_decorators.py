"""
Normalize node class decorators across src/casare_rpa/nodes.

After large-scale refactors/codemods, files can end up with:
- duplicate @properties() decorators
- legacy @trigger_node decorators
- missing/incorrect @node exec_inputs/exec_outputs

This script rewrites the decorator *chunk list* immediately above each top-level
node class into a canonical form:
- exactly one @properties(...) (keeps the most specific one)
- exactly one @node(...) (adds/patches category + exec config)
- no @trigger_node

Usage:
  python scripts/normalize_node_decorators.py --apply
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

RE_CLASS_LINE = re.compile(r"^class\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<bases>[^)]*)\)\s*:\s*$")
RE_DECORATOR_START = re.compile(r"^\s*@")

RE_ADD_EXEC_IN = re.compile(r"\.add_exec_input\s*\(\s*(?P<arg>[^)]*)\)")
RE_ADD_EXEC_OUT = re.compile(r"\.add_exec_output\s*\(\s*(?P<arg>[^)]*)\)")
RE_ADD_IN_EXEC_OLD = re.compile(
    r"\.add_input_port\s*\(\s*['\"](?P<name>[^'\"]+)['\"]\s*,\s*DataType\.EXEC\b"
)
RE_ADD_OUT_EXEC_OLD = re.compile(
    r"\.add_output_port\s*\(\s*['\"](?P<name>[^'\"]+)['\"]\s*,\s*DataType\.EXEC\b"
)


@dataclass(frozen=True)
class DecoratorChunk:
    start: int
    end: int  # exclusive
    text: str
    kind: str  # "node" | "properties" | "trigger_node" | "other"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _nodes_root() -> Path:
    return _repo_root() / "src" / "casare_rpa" / "nodes"


def _iter_py_files() -> Iterable[Path]:
    for p in _nodes_root().rglob("*.py"):
        if any(part in {"__pycache__"} for part in p.parts):
            continue
        if p.name in {"registry_data.py", "__init__.py", "preloader.py"}:
            continue
        yield p


def _derive_category(path: Path) -> str:
    rel = path.relative_to(_nodes_root())
    if len(rel.parts) >= 2:
        top = rel.parts[0]
        if top == "trigger_nodes":
            return "triggers"
        if top == "desktop_nodes":
            return "desktop"
        return top
    # Root-level legacy modules (keep stable categories to avoid palette churn)
    name = path.name
    if name in {"basic_nodes.py"}:
        return "basic"
    if name in {"variable_nodes.py"}:
        return "variable"
    if name in {"wait_nodes.py", "data_nodes.py"}:
        return "browser"
    if name in {"parallel_nodes.py"}:
        return "control_flow"
    if name in {"error_handling_nodes.py"}:
        return "error_handling"
    if name in {"random_nodes.py", "datetime_nodes.py", "utility_nodes.py"}:
        return "utility"
    if name in {"string_nodes.py", "math_nodes.py", "list_nodes.py", "dict_nodes.py"}:
        return "data"
    if name in {"script_nodes.py"}:
        return "scripts"
    if name in {"ftp_nodes.py"}:
        return "file"
    if name in {"pdf_nodes.py", "xml_nodes.py"}:
        return "document"
    return "general"


def _parse_string_arg(arg_text: str, default: str) -> str:
    arg_text = arg_text.strip()
    if not arg_text:
        return default
    m = re.match(r"['\"](?P<s>[^'\"]+)['\"]", arg_text)
    if m:
        return m.group("s")
    return default


def _extract_exec_ports(class_block: str) -> tuple[list[str], list[str]]:
    exec_inputs: list[str] = []
    exec_outputs: list[str] = []

    for m in RE_ADD_EXEC_IN.finditer(class_block):
        name = _parse_string_arg(m.group("arg"), "exec_in")
        if name not in exec_inputs:
            exec_inputs.append(name)

    for m in RE_ADD_EXEC_OUT.finditer(class_block):
        name = _parse_string_arg(m.group("arg"), "exec_out")
        if name not in exec_outputs:
            exec_outputs.append(name)

    for m in RE_ADD_IN_EXEC_OLD.finditer(class_block):
        name = m.group("name")
        if name not in exec_inputs:
            exec_inputs.append(name)

    for m in RE_ADD_OUT_EXEC_OLD.finditer(class_block):
        name = m.group("name")
        if name not in exec_outputs:
            exec_outputs.append(name)

    return exec_inputs, exec_outputs


def _chunk_kind(chunk_text: str) -> str:
    first = chunk_text.lstrip()
    if first.startswith("@trigger_node"):
        return "trigger_node"
    if re.match(r"@\s*properties\b", first):
        return "properties"
    if re.match(r"@\s*node\b", first):
        return "node"
    return "other"


def _read_decorator_chunks(lines: list[str], start_index: int) -> list[DecoratorChunk]:
    """
    Parse consecutive decorator chunks starting at start_index (line begins with '@').
    Each chunk includes continuation lines until paren balance returns to 0.
    """
    chunks: list[DecoratorChunk] = []
    idx = start_index
    while idx < len(lines) and RE_DECORATOR_START.match(lines[idx]):
        chunk_start = idx
        paren = 0
        # Count parens from this line onward until balanced and the next line is not a continuation.
        while idx < len(lines):
            line = lines[idx]
            paren += line.count("(") - line.count(")")
            idx += 1
            if paren <= 0:
                break
        chunk_text = "".join(lines[chunk_start:idx])
        chunks.append(
            DecoratorChunk(
                start=chunk_start,
                end=idx,
                text=chunk_text,
                kind=_chunk_kind(chunk_text),
            )
        )
        # Decorators must be contiguous (no blank line) to apply; stop if blank.
        if idx < len(lines) and lines[idx].strip() == "":
            break
    return chunks


def _format_list(items: list[str]) -> str:
    return "[" + ", ".join(f'"{x}"' for x in items) + "]"


def _build_node_decorator(category: str, exec_inputs: list[str], exec_outputs: list[str]) -> str:
    parts: list[str] = []
    if category != "general":
        parts.append(f'category="{category}"')
    if exec_inputs != ["exec_in"]:
        parts.append(f"exec_inputs={_format_list(exec_inputs)}")
    if exec_outputs != ["exec_out"]:
        parts.append(f"exec_outputs={_format_list(exec_outputs)}")
    if parts:
        return "@node(" + ", ".join(parts) + ")\n"
    return "@node\n"


def _select_best_properties_chunk(
    chunks: list[DecoratorChunk],
) -> DecoratorChunk | None:
    props = [c for c in chunks if c.kind == "properties"]
    if not props:
        return None
    # Prefer a non-empty call over @properties() if present.
    non_empty = [c for c in props if "@properties()" not in c.text.replace(" ", "")]
    if non_empty:
        # Keep the first (outermost) non-empty for stability.
        return non_empty[0]
    return props[0]


def _normalize_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    category = _derive_category(path)
    changed = False

    idx = 0
    while idx < len(lines):
        if lines[idx].startswith("class "):
            m = RE_CLASS_LINE.match(lines[idx].strip("\n"))
            if not m:
                idx += 1
                continue

            class_name = m.group("name")
            bases = m.group("bases")
            if not class_name.endswith("Node") or class_name.startswith("Visual"):
                idx += 1
                continue

            # Decorator *region* must be immediately above the class line with no blank line.
            # This region may include multi-line decorator calls (lines that do not start with '@').
            region_start = idx - 1
            while region_start >= 0 and lines[region_start].strip() != "":
                region_start -= 1
            region_start += 1

            # Find the first decorator line within the contiguous region.
            dec_start = None
            for j in range(region_start, idx):
                if RE_DECORATOR_START.match(lines[j]):
                    dec_start = j
                    break
            if dec_start is None:
                idx += 1
                continue

            # Parse consecutive decorator chunks starting at dec_start.
            chunks = _read_decorator_chunks(lines, dec_start)
            if not chunks:
                idx += 1
                continue

            # Extract class block for exec port inference.
            block_end = idx + 1
            while block_end < len(lines) and not lines[block_end].startswith("class "):
                block_end += 1
            class_block = "".join(lines[idx:block_end])

            exec_inputs, exec_outputs = _extract_exec_ports(class_block)
            if not exec_inputs:
                exec_inputs = ["exec_in"]
            if not exec_outputs:
                exec_outputs = ["exec_out"]

            # Trigger nodes: enforce no exec_in.
            if "BaseTriggerNode" in bases or "trigger_nodes" in str(path).replace("\\", "/"):
                exec_inputs = []
                exec_outputs = ["exec_out"]

            best_props = _select_best_properties_chunk(chunks)
            [c for c in chunks if c.kind == "node"]

            # Build canonical decorator text (properties first, node second).
            canonical: list[str] = []
            if best_props is None:
                canonical.append("@properties()\n")
            else:
                canonical.append(best_props.text)
                if not best_props.text.endswith("\n"):
                    canonical.append("\n")

            canonical.append(_build_node_decorator(category, exec_inputs, exec_outputs))

            # Replace original decorator region with canonical if different.
            dec_region_start = chunks[0].start
            dec_region_end = chunks[-1].end
            original_region = "".join(lines[dec_region_start:dec_region_end])
            new_region = "".join(canonical)
            if original_region != new_region:
                lines[dec_region_start:dec_region_end] = new_region.splitlines(keepends=True)
                changed = True
                # Adjust idx to point at class line after replacement.
                idx = dec_region_start + 1
                continue

        idx += 1

    if not changed:
        return False

    path.write_text("".join(lines), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--file",
        type=str,
        default="",
        help="Normalize only one file (path relative to repo root).",
    )
    args = ap.parse_args()
    if not args.apply:
        ap.error("Use --apply")

    changed = 0
    if args.file:
        files = [(_repo_root() / args.file).resolve()]
    else:
        files = list(_iter_py_files())
    for p in files:
        print(f"Normalizing: {p}")
        if _normalize_file(p):
            changed += 1
    print(f"Scanned: {len(files)} files")
    print(f"Normalized: {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
