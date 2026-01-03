"""Domain-level interface for retrieving node manifest documentation."""

from __future__ import annotations

from typing import Protocol


class INodeManifestProvider(Protocol):
    """Provides a compact node manifest suitable for prompting."""

    def get_compact_markdown(self) -> str: ...
