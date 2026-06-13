"""
Readable manifest diff for `cook --diff`. Legible edits: surface concrete
before/after values so any change is explainable in a sentence.
"""
from __future__ import annotations

from .manifest import Manifest


def diff_manifests(a: Manifest, b: Manifest) -> str:
    lines = [f"diff: v{a.version} -> v{b.version}",
             f"  changelog(v{b.version}): {b.changelog}"]

    sa, sb = a.song, b.song
    for fld in ("key", "scale", "bpm", "chaos", "global_swing", "genre_spec"):
        va, vb = getattr(sa, fld), getattr(sb, fld)
        if va != vb:
            lines.append(f"  song.{fld}: {va} -> {vb}")

    # Sections
    if len(sa.sections) != len(sb.sections):
        lines.append(f"  sections: {len(sa.sections)} -> {len(sb.sections)}")
    for i in range(min(len(sa.sections), len(sb.sections))):
        seca, secb = sa.sections[i], sb.sections[i]
        if seca.energy != secb.energy:
            lines.append(f"  section[{i}] {secb.type} energy: {seca.energy} -> {secb.energy}")
        if seca.length_bars != secb.length_bars:
            lines.append(f"  section[{i}] {secb.type} bars: "
                         f"{seca.length_bars} -> {secb.length_bars}")
        if seca.progression != secb.progression:
            lines.append(f"  section[{i}] {secb.type} progression: "
                         f"{seca.progression} -> {secb.progression}")

    # Stems: note counts per role
    roles = {s.role for s in sa.stems} | {s.role for s in sb.stems}
    for role in sorted(roles):
        na = len(a.song.stem(role).notes) if a.song.stem(role) else 0
        nb = len(b.song.stem(role).notes) if b.song.stem(role) else 0
        if na != nb:
            lines.append(f"  stem[{role}] notes: {na} -> {nb}")

    if len(lines) == 2:
        lines.append("  (no structural differences)")
    return "\n".join(lines)
