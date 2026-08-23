"""WentiPack registry + loader.

A 文体 pack is a hand-curated markdown file (`<name>.md`) with a YAML
frontmatter carrying the structured contract (lineage, voice_card,
few_shots) and a human-readable body of voice notes. The loader resolves
packs from a registry (`index.yaml`) and parses them into typed dicts so
the scorer never has to touch markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_PACKS_DIR = Path(__file__).resolve().parent


@dataclass
class FewShot:
    """A curated 三联-style paragraph the model imitates."""

    text: str
    note: str = ""


@dataclass
class WentiPack:
    """A named, curated 中文 editorial-voice unit (the core primitive)."""

    name: str
    lineage: str
    voice_card: str
    few_shots: list[FewShot] = field(default_factory=list)
    notes: str = ""

    def to_prompt_block(self) -> str:
        """Render the pack as a compact prompt block for the LLM judge."""
        shots = "\n\n".join(
            f"【范例 {i + 1}】{shot.text.strip()}"
            for i, shot in enumerate(self.few_shots)
        )
        return (
            f"文体：{self.lineage}（pack id: {self.name}）\n"
            f"编辑视角（voice card）：\n{self.voice_card.strip()}\n\n"
            f"curated 范例（few-shots，模仿其句式/用词/节奏/视角）：\n{shots}"
        )


def _parse_pack_doc(text: str) -> tuple[dict[str, Any], str]:
    """Split a pack markdown into (frontmatter, body)."""
    if not text.startswith("---"):
        raise ValueError("pack markdown must start with a '---' frontmatter fence")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("pack markdown is missing the closing '---' fence")
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def load_pack(name: str, packs_dir: Path | None = None) -> WentiPack:
    """Load a WentiPack by its ASCII id (e.g. ``sanlian``)."""
    root = packs_dir or _PACKS_DIR
    path = root / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"文体 pack not found: {name} (looked at {path})")
    meta, body = _parse_pack_doc(path.read_text(encoding="utf-8"))
    shots_raw = meta.get("few_shots", []) or []
    few_shots = [
        FewShot(text=s.get("text", ""), note=s.get("note", ""))
        for s in shots_raw
        if isinstance(s, dict) and s.get("text")
    ]
    return WentiPack(
        name=meta.get("name", name),
        lineage=meta.get("lineage", name),
        voice_card=meta.get("voice_card", ""),
        few_shots=few_shots,
        notes=body,
    )


def list_packs(packs_dir: Path | None = None) -> list[dict[str, Any]]:
    """Return the pack registry entries from ``index.yaml``."""
    root = packs_dir or _PACKS_DIR
    index_path = root / "index.yaml"
    registry = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    return registry.get("packs", []) or []


__all__ = ["FewShot", "WentiPack", "load_pack", "list_packs"]
