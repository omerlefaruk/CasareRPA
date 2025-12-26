"""Lazy context loading utilities for .brain/ context files.

Provides on-demand loading of context files to reduce token usage.
"""

from datetime import datetime
from pathlib import Path


class ContextLoader:
    """Lazy loader for .brain/ context files.

    Loads only the minimum necessary context:
    - current.md: Always loaded (active session)
    - recent.md: Loaded on demand
    - archive/: Never loaded (reference only)

    Usage:
        loader = ContextLoader()
        current = loader.load_current()

        # Load additional context only if needed
        if need_history:
            recent = loader.load_recent()
    """

    def __init__(self, brain_dir: Path | None = None):
        """Initialize context loader.

        Args:
            brain_dir: Path to .brain/ directory. Default: .brain/
        """
        if brain_dir is None:
            brain_dir = Path(__file__).parent.parent / ".brain"

        self.brain_dir = Path(brain_dir)
        self.context_dir = self.brain_dir / "context"

    def load_current(self) -> str:
        """Load current context file.

        Returns:
            Content of context/current.md

        Example:
            >>> loader = ContextLoader()
            >>> current = loader.load_current()
            >>> print(current)
            # Current Context...
        """
        current_path = self.context_dir / "current.md"

        if not current_path.exists():
            return "# No current context"

        return current_path.read_text(encoding="utf-8")

    def load_recent(self) -> str:
        """Load recent context file.

        Returns:
            Content of context/recent.md

        Example:
            >>> loader = ContextLoader()
            >>> recent = loader.load_recent()
            >>> print(recent)
            # Recent Completed Tasks...
        """
        recent_path = self.context_dir / "recent.md"

        if not recent_path.exists():
            return "# No recent context"

        return recent_path.read_text(encoding="utf-8")

    def load_archive(self, filename: str) -> str:
        """Load specific archive file.

        Args:
            filename: Name of file in context/archive/

        Returns:
            Content of archive file

        Example:
            >>> loader = ContextLoader()
            >>> archived = loader.load_archive('activeContext-2025-12-09-full.md')
        """
        archive_path = self.context_dir / "archive" / filename

        if not archive_path.exists():
            return f"# Archive file not found: {filename}"

        return archive_path.read_text(encoding="utf-8")

    def list_archives(self) -> list[str]:
        """List all available archive files.

        Returns:
            List of archive filenames sorted by date (newest first)

        Example:
            >>> loader = ContextLoader()
            >>> archives = loader.list_archives()
            >>> print(archives)
            ['activeContext-2025-12-25.md', 'activeContext-2025-12-09.md', ...]
        """
        archive_dir = self.context_dir / "archive"

        if not archive_dir.exists():
            return []

        files = list(archive_dir.glob("*.md"))
        files.sort(reverse=True)

        return [f.name for f in files]

    def get_minimal_context(self) -> str:
        """Get minimal context for agent invocation.

        Returns only current.md (most common case).
        """
        return self.load_current()

    def get_full_context(self) -> str:
        """Get full context (current + recent).

        Use sparingly - only when historical context is needed.
        """
        current = self.load_current()
        recent = self.load_recent()

        return f"{current}\n\n{recent}"

    def archive_current(self, suffix: str | None = None) -> Path:
        """Archive current context and create new current.md.

        Args:
            suffix: Optional suffix for archive filename.

        Returns:
            Path to archived file

        Example:
            >>> loader = ContextLoader()
            >>> loader.archive_current(suffix='completed-session')
            >>> new_current = loader.load_current()
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"activeContext-{timestamp}"
        if suffix:
            filename += f"-{suffix}"
        filename += ".md"

        archive_dir = self.context_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        archive_path = archive_dir / filename
        current_path = self.context_dir / "current.md"

        if current_path.exists():
            current_content = current_path.read_text(encoding="utf-8")
            archive_path.write_text(current_content, encoding="utf-8")

            template = """# Current Context

**Updated**: {timestamp} | **Branch**: main

## Active Work
- **Focus**: [Description of current work]
- **Status**: [In Progress | Planning | Complete]
- **Plan**: `[path/to/plan.md]`
- **Area**: `[area of codebase]`

## Completed This Session ({timestamp})

### [Task 1 Title]

1. **Description of what was done**
   - Details...
   - More details...

### [Task 2 Title]

...

## Quick References
- **Full Guide**: `[path/to/guide.md]`
- **Context**: `.brain/context/current.md` (this file)
- **Patterns**: `.brain/systemPatterns.md`

## Notes
<!-- Add session-specific notes here. Clear after session. -->

## Phase Report ({timestamp})
Phase: [Planning | Build | QA | Docs]
In progress: [Description]
Completed:
- [What was completed]
Result: [Outcome]

## Next Steps
1. [Next step 1]
2. [Next step 2]
"""

            current_path.write_text(
                template.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M UTC")),
                encoding="utf-8",
            )

        return archive_path

    def update_recent(self, task_summary: str) -> None:
        """Update recent.md with new completed task.

        Args:
            task_summary: Markdown summary of completed task

        Example:
            >>> loader = ContextLoader()
            >>> summary = "## New Task\\n**Status**: COMPLETE\\n- Completed feature..."
            >>> loader.update_recent(summary)
        """
        recent_path = self.context_dir / "recent.md"

        if not recent_path.exists():
            template = """# Recent Completed Tasks

Last 3 completed tasks (summarized). Full details in archive.

---

"""
            recent_path.write_text(template, encoding="utf-8")

        current_content = recent_path.read_text(encoding="utf-8")

        lines = current_content.split("\n")
        entries = []

        current_entry = []
        in_entry = False

        for line in lines:
            if line.startswith("##"):
                if in_entry:
                    entries.append("\n".join(current_entry))
                current_entry = [line]
                in_entry = True
            elif in_entry:
                current_entry.append(line)

        if current_entry:
            entries.append("\n".join(current_entry))

        entries.insert(0, task_summary)

        if len(entries) > 3:
            entries = entries[:3]

        header = lines[:4]
        new_content = "\n".join(header) + "\n\n".join(entries)

        recent_path.write_text(new_content, encoding="utf-8")


def load_context_for_agent(need_recent: bool = False, need_archive: str | None = None) -> str:
    """Convenience function for agent context loading.

    Args:
        need_recent: Include recent.md in context
        need_archive: Specific archive file to load

    Returns:
        Combined context string

    Example:
        >>> # Default: just current.md
        >>> context = load_context_for_agent()

        >>> # With recent
        >>> context = load_context_for_agent(need_recent=True)

        >>> # Specific archive
        >>> context = load_context_for_agent(need_archive='old-session.md')
    """
    loader = ContextLoader()
    context = loader.load_current()

    if need_recent:
        context += f"\n\n{loader.load_recent()}"

    if need_archive:
        context += f"\n\n{loader.load_archive(need_archive)}"

    return context
