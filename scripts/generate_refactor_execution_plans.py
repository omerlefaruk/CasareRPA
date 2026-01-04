#!/usr/bin/env python3
"""
Generate folder-by-folder, file-by-file execution plans for the refactor program.

Outputs:
  plans/refactor-execution/_index.md
  plans/refactor-execution/00-latest-changes.md
  plans/refactor-execution/10-python-domain.md
  plans/refactor-execution/11-python-application.md
  plans/refactor-execution/12-python-infrastructure.md
  plans/refactor-execution/13-python-presentation.md
  plans/refactor-execution/20-dashboard.md
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ImportHit:
    filepath: Path
    lineno: int
    module: str
    line: str
    in_type_checking: bool


def _repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return Path(out)
    except Exception:
        return Path(__file__).resolve().parent.parent


def _run_git(root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True)
    except Exception:
        return ""


def _read_text_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _py_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*.py")
        if "__pycache__" not in str(p) and p.is_file()
    )


def _dashboard_files(root: Path) -> list[Path]:
    exts = {".ts", ".tsx", ".js", ".jsx", ".css", ".md"}
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in exts
        and "node_modules" not in str(p)
        and "dist" not in str(p)
    )


def _iter_import_nodes(tree: ast.AST) -> Iterable[ast.AST]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node


def _is_type_checking_if(node: ast.If) -> bool:
    # Matches: if TYPE_CHECKING:
    test = node.test
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def _collect_import_hits(path: Path) -> list[ImportHit]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []

    # Determine line ranges that are inside `if TYPE_CHECKING:` blocks.
    type_checking_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_type_checking_if(node):
            for child in ast.walk(node):
                if hasattr(child, "lineno") and hasattr(child, "end_lineno"):
                    for ln in range(child.lineno, child.end_lineno + 1):  # type: ignore[attr-defined]
                        type_checking_lines.add(int(ln))

    hits: list[ImportHit] = []
    for node in _iter_import_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                lineno = int(getattr(node, "lineno", 0) or 0)
                line = lines[lineno - 1].strip() if 1 <= lineno <= len(lines) else ""
                hits.append(
                    ImportHit(
                        filepath=path,
                        lineno=lineno,
                        module=module,
                        line=line,
                        in_type_checking=lineno in type_checking_lines,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            lineno = int(getattr(node, "lineno", 0) or 0)
            line = lines[lineno - 1].strip() if 1 <= lineno <= len(lines) else ""
            hits.append(
                ImportHit(
                    filepath=path,
                    lineno=lineno,
                    module=module,
                    line=line,
                    in_type_checking=lineno in type_checking_lines,
                )
            )
    return hits


def _violations_for_layer(
    files: list[Path],
    forbidden_prefixes: tuple[str, ...],
    allow_path_contains: tuple[str, ...] = (),
    allow_in_type_checking: bool = True,
) -> list[ImportHit]:
    violations: list[ImportHit] = []
    for file in files:
        rel = file.as_posix()
        if allow_path_contains and any(token in rel for token in allow_path_contains):
            continue
        for hit in _collect_import_hits(file):
            if allow_in_type_checking and hit.in_type_checking:
                continue
            if any(hit.module.startswith(prefix) for prefix in forbidden_prefixes):
                violations.append(hit)
    return violations


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _md_file_list(title: str, root: Path, files: list[Path]) -> str:
    rels = [p.relative_to(root).as_posix() for p in files]
    lines = [f"# {title}", "", f"Root: `{root.as_posix()}`", "", "## Files", ""]
    lines.extend([f"- `{r}`" for r in rels])
    return "\n".join(lines)


def main() -> int:
    root = _repo_root()
    plans_dir = root / "plans" / "refactor-execution"

    # Latest changes snapshot (working tree)
    git_log = _run_git(root, ["log", "-n", "20", "--oneline", "--decorate"]).strip()
    git_stat = _run_git(root, ["diff", "--stat"]).strip()
    git_name_status = _run_git(root, ["diff", "--name-status"]).strip()

    _write_md(
        plans_dir / "00-latest-changes.md",
        "\n".join(
            [
                "# Latest Changes Snapshot",
                "",
                "This is an auto-generated snapshot of recent commits and current working tree diffs.",
                "",
                "## Recent commits",
                "",
                "```text",
                git_log,
                "```",
                "",
                "## Working tree diff (name-status)",
                "",
                "```text",
                git_name_status,
                "```",
                "",
                "## Working tree diff (stat)",
                "",
                "```text",
                git_stat,
                "```",
            ]
        ),
    )

    src_root = root / "src" / "casare_rpa"
    domain_root = src_root / "domain"
    app_root = src_root / "application"
    infra_root = src_root / "infrastructure"
    pres_root = src_root / "presentation"

    domain_files = _py_files(domain_root) if domain_root.exists() else []
    app_files = _py_files(app_root) if app_root.exists() else []
    infra_files = _py_files(infra_root) if infra_root.exists() else []
    pres_files = _py_files(pres_root) if pres_root.exists() else []

    domain_violations = _violations_for_layer(
        domain_files,
        forbidden_prefixes=(
            "casare_rpa.application",
            "casare_rpa.infrastructure",
            "casare_rpa.presentation",
        ),
        allow_path_contains=("domain/port_type_system.py",),
    )
    app_violations = _violations_for_layer(
        app_files,
        forbidden_prefixes=("casare_rpa.infrastructure", "casare_rpa.presentation"),
        allow_path_contains=("application/dependency_injection/",),
    )
    pres_violations = _violations_for_layer(
        pres_files,
        forbidden_prefixes=("casare_rpa.infrastructure",),
        allow_path_contains=(
            "presentation/canvas/app.py",
            "presentation/canvas/main.py",
            "presentation/setup/",
            "application/dependency_injection/",
        ),
        allow_in_type_checking=True,
    )

    _write_md(
        plans_dir / "10-python-domain.md",
        "\n".join(
            [
                "# Execution Plan: Python Domain",
                "",
                f"Root: `{domain_root.as_posix()}`",
                "",
                "## Boundary violations (domain imports outer layers)",
                "",
                "This list is auto-detected and should trend to zero over time.",
                "",
                *(
                    ["- None detected"]
                    if not domain_violations
                    else [
                        f"- `{h.filepath.relative_to(root).as_posix()}:{h.lineno}` imports `{h.module}`"
                        for h in domain_violations
                    ]
                ),
                "",
                "## File inventory",
                "",
                *[f"- `{p.relative_to(root).as_posix()}`" for p in domain_files],
            ]
        ),
    )

    _write_md(
        plans_dir / "11-python-application.md",
        "\n".join(
            [
                "# Execution Plan: Python Application",
                "",
                f"Root: `{app_root.as_posix()}`",
                "",
                "## Boundary violations (application imports outer layers)",
                "",
                "Auto-detected imports from `infrastructure/` or `presentation/` outside the DI composition root.",
                "",
                *(
                    ["- None detected"]
                    if not app_violations
                    else [
                        f"- `{h.filepath.relative_to(root).as_posix()}:{h.lineno}` imports `{h.module}`"
                        for h in app_violations
                    ]
                ),
                "",
                "## File inventory",
                "",
                *[f"- `{p.relative_to(root).as_posix()}`" for p in app_files],
            ]
        ),
    )

    _write_md(
        plans_dir / "12-python-infrastructure.md",
        _md_file_list("Execution Plan: Python Infrastructure", infra_root, infra_files),
    )

    _write_md(
        plans_dir / "13-python-presentation.md",
        "\n".join(
            [
                "# Execution Plan: Python Presentation",
                "",
                f"Root: `{pres_root.as_posix()}`",
                "",
                "## Boundary violations (presentation imports infrastructure)",
                "",
                "Auto-detected direct infrastructure imports (allowed only in composition roots).",
                "",
                *(
                    ["- None detected"]
                    if not pres_violations
                    else [
                        f"- `{h.filepath.relative_to(root).as_posix()}:{h.lineno}` imports `{h.module}`"
                        for h in pres_violations
                    ]
                ),
                "",
                "## File inventory",
                "",
                *[f"- `{p.relative_to(root).as_posix()}`" for p in pres_files],
            ]
        ),
    )

    dashboard_root = root / "monitoring-dashboard"
    dashboard_src_root = dashboard_root / "src"
    dashboard_files = (
        _dashboard_files(dashboard_src_root) if dashboard_src_root.exists() else []
    )

    _write_md(
        plans_dir / "20-dashboard.md",
        "\n".join(
            [
                "# Execution Plan: Monitoring Dashboard",
                "",
                f"Root: `{dashboard_root.as_posix()}`",
                "",
                "## Immediate gates",
                "",
                "- `npm ci` must succeed from `package-lock.json` (no committed `node_modules` reliance).",
                "- `npm run lint` must succeed (ESLint flat config).",
                "- `npm run build` must succeed (TypeScript + Vite).",
                "",
                "## File inventory (`monitoring-dashboard/src/`)",
                "",
                *[f"- `{p.relative_to(root).as_posix()}`" for p in dashboard_files],
            ]
        ),
    )

    _write_md(
        plans_dir / "_index.md",
        "\n".join(
            [
                "# Refactor Execution Plans (Folder-by-Folder)",
                "",
                "These files are auto-generated execution plans used to drive the refactor work in small, verifiable steps.",
                "",
                "## Index",
                "",
                "- `plans/refactor-execution/00-latest-changes.md`",
                "- `plans/refactor-execution/10-python-domain.md`",
                "- `plans/refactor-execution/11-python-application.md`",
                "- `plans/refactor-execution/12-python-infrastructure.md`",
                "- `plans/refactor-execution/13-python-presentation.md`",
                "- `plans/refactor-execution/20-dashboard.md`",
            ]
        ),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
