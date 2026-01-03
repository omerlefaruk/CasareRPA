from __future__ import annotations

from casare_rpa.domain.interfaces.node_manifest import INodeManifestProvider
from casare_rpa.infrastructure.ai.registry_dumper import (
    dump_node_manifest,
    manifest_to_compact_markdown,
)


class NodeManifestProvider(INodeManifestProvider):
    def get_compact_markdown(self) -> str:
        manifest = dump_node_manifest()
        return manifest_to_compact_markdown(manifest)
