"""
`cook` — single CLI entry point for CRYSTAL COOK.

Stage 2 implements: --key --bpm --genre --chaos --seed --form --swing
--from --diff --stats --freeze-profile.

--sample (Stage 8) and --inspire (Stage 8) are recognized but not yet
implemented; they print a clear stage notice.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import diff as diff_mod
from .engine import stats as stats_mod
from .engine.cook import CookParams, cook, recook_from_manifest
from .engine.manifest import load_manifest
from .engine.profile import freeze_resolved


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cook", description="CRYSTAL COOK — beat generator")
    p.add_argument("--key", default=None, help="Root key, e.g. F#")
    p.add_argument("--bpm", type=float, default=None, help="Tempo (defaults to genre profile)")
    p.add_argument("--genre", default="trap",
                   help="Profile name or blend, e.g. 'trap' or 'trap:0.6+boombap:0.4'")
    p.add_argument("--chaos", type=float, default=0.0, help="Experimental knob 0..1")
    p.add_argument("--seed", type=int, default=None, help="Reproducibility seed")
    p.add_argument("--form", default=None, help="Override song form string")
    p.add_argument("--swing", type=float, default=None, help="Override global swing 0..1")
    # Co-producer / utility modes (each takes over when present):
    p.add_argument("--from", dest="from_manifest", default=None,
                   help="Re-render MIDI from a manifest (path to cook.json / cook_vN.json)")
    p.add_argument("--diff", nargs=2, metavar=("A", "B"), default=None,
                   help="Readable diff between two manifest files")
    p.add_argument("--stats", default=None, help="Per-section summary for a manifest")
    p.add_argument("--freeze-profile", nargs=2, dest="freeze", metavar=("MANIFEST", "NAME"),
                   default=None, help="Write a cook's resolved params as a named profile")
    # Stage 8 (recognized, not yet implemented):
    p.add_argument("--sample", default=None, help="(Stage 8) seed a cook from a chop folder")
    p.add_argument("--inspire", default=None, help="(Stage 8) derive a reference profile from audio")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # ── Utility / co-producer modes ──
    if args.stats:
        m = load_manifest(Path(args.stats))
        print(stats_mod.format_stats(m))
        return 0

    if args.diff:
        a = load_manifest(Path(args.diff[0]))
        b = load_manifest(Path(args.diff[1]))
        print(diff_mod.diff_manifests(a, b))
        return 0

    if args.freeze:
        manifest_path, name = args.freeze
        m = load_manifest(Path(manifest_path))
        out = freeze_resolved(m.song.genre_spec, name,
                              overrides={"bpm": m.song.bpm, "swing": m.song.global_swing})
        print(f"Froze resolved profile for '{m.song.genre_spec}' -> {out}")
        return 0

    if args.from_manifest:
        out = recook_from_manifest(Path(args.from_manifest))
        print(f"Re-rendered -> {out}")
        return 0

    if args.sample:
        print("--sample is a Stage 8 feature (sample chopper handoff). Not yet implemented.")
        return 2

    if args.inspire:
        print("--inspire is a Stage 8 feature (reference profile). Not yet implemented.")
        return 2

    # ── Default: run a cook ──
    params = CookParams(
        genre=args.genre, key=args.key, bpm=args.bpm, chaos=args.chaos,
        seed=args.seed, form=args.form, swing=args.swing,
    )
    cook_dir, manifest = cook(params)
    s = manifest.song
    print(f"Cooked: {cook_dir}")
    print(f"  {s.key} {s.scale}  {s.bpm} BPM  genre={s.genre_spec}  "
          f"chaos={s.chaos}  seed={s.seed}")
    print(f"  form: {' '.join(f'{x.type}({x.length_bars})' for x in s.sections)}")
    print(f"  stems: {', '.join(st.role + f'({len(st.notes)})' for st in s.stems)}")
    print(f"  ending: {manifest.ending_mode}")
    print(f"  manifest: {cook_dir / 'cook.json'}")
    print(f"  midi:     {cook_dir / 'output.mid'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
