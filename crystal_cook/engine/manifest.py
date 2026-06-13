"""
Cook manifest: cook.json fully determines the output (the manifest IS the
beat). Re-rendering from a manifest is deterministic because realized note
data is stored, not just rules.

Versioning, never destruction: edits write cook_v2.json, cook_v3.json, ...
each with a `parent` field and a one-line `changelog`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .model import Section, Song, Stem

SCHEMA = "crystal-cook/1"


@dataclass
class Manifest:
    name: str
    song: Song
    ending_mode: str = "dry"
    version: int = 1
    parent: Optional[int] = None
    changelog: str = "initial cook"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cast_presets: dict = field(default_factory=dict)     # Stage 4: role -> preset
    matched_samples: list = field(default_factory=list)  # Stage 5

    # ── serialization ──
    def to_dict(self) -> dict:
        s = self.song
        return {
            "schema": SCHEMA,
            "version": self.version,
            "parent": self.parent,
            "changelog": self.changelog,
            "name": self.name,
            "created": self.created,
            "ending_mode": self.ending_mode,
            "song": {
                "key": s.key,
                "scale": s.scale,
                "bpm": s.bpm,
                "seed": s.seed,
                "chaos": s.chaos,
                "genre_spec": s.genre_spec,
                "global_swing": s.global_swing,
                "sections": [sec.to_dict() for sec in s.sections],
                "stems": [st.to_dict() for st in s.stems],
            },
            "cast_presets": self.cast_presets,
            "matched_samples": self.matched_samples,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Manifest":
        sd = d["song"]
        song = Song(
            key=sd["key"], scale=sd["scale"], bpm=sd["bpm"], seed=sd["seed"],
            chaos=sd["chaos"], genre_spec=sd["genre_spec"],
            global_swing=sd["global_swing"],
            sections=[Section.from_dict(x) for x in sd["sections"]],
            stems=[Stem.from_dict(x) for x in sd["stems"]],
        )
        return cls(
            name=d["name"], song=song, ending_mode=d.get("ending_mode", "dry"),
            version=d.get("version", 1), parent=d.get("parent"),
            changelog=d.get("changelog", ""), created=d.get("created", ""),
            cast_presets=d.get("cast_presets", {}),
            matched_samples=d.get("matched_samples", []),
        )

    # ── files ──
    def filename(self) -> str:
        return "cook.json" if self.version == 1 else f"cook_v{self.version}.json"

    def save(self, cook_dir: Path) -> Path:
        cook_dir.mkdir(parents=True, exist_ok=True)
        path = cook_dir / self.filename()
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path


def load_manifest(path: Path) -> Manifest:
    with open(path) as f:
        return Manifest.from_dict(json.load(f))


def next_version_path(cook_dir: Path) -> int:
    """Determine the next version number in a cook folder."""
    versions = [1] if (cook_dir / "cook.json").exists() else [0]
    for p in cook_dir.glob("cook_v*.json"):
        try:
            versions.append(int(p.stem.split("v")[-1]))
        except ValueError:
            pass
    return max(versions) + 1
