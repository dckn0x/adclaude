"""
Deaf-agent guardrails: per-section density/register/brightness/energy summaries
so the co-producer can sanity-check structure without ears ("is the hook
actually bigger than the verse?").
"""
from __future__ import annotations

from .macros import CUTOFF
from .manifest import Manifest
from .model import MELODIC_ROLES, Role


def section_stats(manifest: Manifest) -> list[dict]:
    song = manifest.song
    out = []
    for si, sec in enumerate(song.sections):
        bars = sec.length_bars
        per_role = {}
        total_notes = 0
        pitches = []
        brightness_vals = []
        for stem in song.stems:
            notes = [n for n in stem.notes if n.section_index == si]
            if not notes:
                continue
            total_notes += len(notes)
            per_role[stem.role] = {
                "notes": len(notes),
                "density_per_bar": round(len(notes) / bars, 2),
            }
            if stem.role in (r.value for r in MELODIC_ROLES):
                pitches += [n.pitch for n in notes]
            # brightness proxy: mean CUTOFF gesture value in this section
            for g in stem.gestures:
                if g.target_cc == CUTOFF and g.start_beat >= song.section_beat_range(si)[0] \
                        and g.start_beat < song.section_beat_range(si)[1]:
                    brightness_vals.append((g.value_start + g.value_end) / 2)

        out.append({
            "index": si,
            "type": sec.type,
            "bars": bars,
            "energy": sec.energy,
            "total_notes": total_notes,
            "density_per_bar": round(total_notes / bars, 2),
            "register": {
                "min": min(pitches) if pitches else None,
                "max": max(pitches) if pitches else None,
                "mean": round(sum(pitches) / len(pitches), 1) if pitches else None,
            },
            "brightness": round(sum(brightness_vals) / len(brightness_vals), 1)
                          if brightness_vals else None,
            "roles": per_role,
        })
    return out


def format_stats(manifest: Manifest) -> str:
    rows = section_stats(manifest)
    lines = [f"COOK {manifest.name}  (v{manifest.version})",
             f"key={manifest.song.key} {manifest.song.scale}  "
             f"bpm={manifest.song.bpm}  chaos={manifest.song.chaos}  "
             f"seed={manifest.song.seed}",
             ""]
    header = f"{'#':>2} {'TYPE':<10} {'bars':>4} {'energy':>6} {'notes':>5} " \
             f"{'n/bar':>6} {'reg(min-max)':>13} {'bright':>6}"
    lines.append(header)
    lines.append("-" * len(header))
    for r in rows:
        reg = r["register"]
        reg_s = f"{reg['min']}-{reg['max']}" if reg["min"] is not None else "-"
        bright = r["brightness"] if r["brightness"] is not None else "-"
        lines.append(
            f"{r['index']:>2} {r['type']:<10} {r['bars']:>4} {r['energy']:>6} "
            f"{r['total_notes']:>5} {r['density_per_bar']:>6} {reg_s:>13} {bright:>6}"
        )
    return "\n".join(lines)
