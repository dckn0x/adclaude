#!/usr/bin/env python3
"""
Stage 1 spike: verify pyflp can round-trip an FL Studio project.

Usage:
    # Generate a self-contained minimal test FLP (no template needed):
    python -m crystal_cook.spike.stage1_pyflp_test

    # Test against YOUR template.flp:
    python -m crystal_cook.spike.stage1_pyflp_test --template /path/to/template.flp

Both modes produce an output file you can open in FL Studio to confirm success.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# Apply pyflp Python 3.11 compat patch first
from crystal_cook.compat import patch as _patch_pyflp
_patch_pyflp()

import pyflp
import construct as c
from pyflp._events import (
    EventTree, IndexedEvent, AsciiEvent, UnicodeEvent,
    U16Event, U32Event, DATA, TEXT,
)
from pyflp.project import FileFormat, ProjectID, VALID_PPQS
from pyflp.pattern import PatternID, NotesEvent


# ── Minimal FLP construction ──────────────────────────────────────────────────

def _varint(n: int) -> bytes:
    result = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)


def _ascii_ev(event_id: int, text: str) -> bytes:
    encoded = (text + "\0").encode("ascii")
    return bytes([event_id]) + _varint(len(encoded)) + encoded


def _unicode_ev(event_id: int, text: str) -> bytes:
    encoded = (text + "\0").encode("utf-16-le")
    return bytes([event_id]) + _varint(len(encoded)) + encoded


def _dword_ev(event_id: int, value: int) -> bytes:
    return bytes([event_id]) + struct.pack("<I", value)


def _word_ev(event_id: int, value: int) -> bytes:
    return bytes([event_id]) + struct.pack("<H", value)


def _data_ev(event_id: int, data: bytes) -> bytes:
    return bytes([event_id]) + _varint(len(data)) + data


def _build_note_bytes() -> bytes:
    """Build a single C4 quarter-note at position 0."""
    NOTE_STRUCT = c.Struct(
        "position" / c.Int32ul,
        "flags" / c.Int16ul,
        "rack_channel" / c.Int16ul,
        "length" / c.Int32ul,
        "key" / c.Int16ul,
        "group" / c.Int16ul,
        "fine_pitch" / c.Int8ul,
        "_u1" / c.Byte,
        "release" / c.Int8ul,
        "midi_channel" / c.Int8ul,
        "pan" / c.Int8ul,
        "velocity" / c.Int8ul,
        "mod_x" / c.Int8ul,
        "mod_y" / c.Int8ul,
    )
    note = dict(
        position=0,
        flags=0,
        rack_channel=0,
        length=96,   # 1 beat @ 96 PPQ
        key=60,      # C4 / middle C
        group=0,
        fine_pitch=64,
        _u1=0,
        release=64,
        midi_channel=0,
        pan=64,
        velocity=100,
        mod_x=128,
        mod_y=128,
    )
    return c.GreedyRange(NOTE_STRUCT).build([note])


def _build_minimal_flp(bpm: float = 140.0, fl_version: str = "25.2.5") -> bytes:
    """
    Construct the smallest valid .flp that FL Studio should be able to open.
    Contains one pattern with one C4 quarter-note on channel 0.
    """
    events = bytearray()

    # Project metadata (FLVersion MUST come first — it sets the string encoding)
    events += _ascii_ev(199, fl_version)                          # FLVersion (always ASCII)
    events += _dword_ev(156, int(bpm * 1000))                     # Tempo
    events += _unicode_ev(194, "crystal-cook-spike")              # Title
    events += _dword_ev(159, 5319)                                # FLBuild (match 25.2.5.5319)

    # One minimal channel (required so pyflp.save() doesn't raise NoModelsFound)
    events += _word_ev(64, 0)                                     # Channel.New IID=0

    # One pattern: PatternID.New(1) + PatternID.Notes(data)
    events += _word_ev(65, 1)                                     # Pattern.New IID=1
    events += _unicode_ev(193, "Stage1 Spike")                    # Pattern.Name
    events += _data_ev(224, _build_note_bytes())                  # Pattern.Notes

    FLP_HEADER = struct.Struct("4sIhHH")
    header = FLP_HEADER.pack(b"FLhd", 6, 0, 0, 96)
    data_size = struct.pack("<I", len(events))
    return header + b"FLdt" + data_size + bytes(events)


# ── Spike logic ───────────────────────────────────────────────────────────────

def run_from_scratch(out_path: Path) -> bool:
    """Generate a minimal FLP from scratch, parse it back, confirm round-trip."""
    print("[Stage 1] Building minimal FLP from scratch...")
    raw = _build_minimal_flp()
    tmp = out_path.parent / "_spike_tmp.flp"
    tmp.write_bytes(raw)

    print(f"  Written {len(raw)} bytes → {tmp}")

    try:
        proj = pyflp.parse(tmp)
    except Exception as e:
        print(f"  FAIL — pyflp.parse() raised: {e}")
        return False

    print(f"  Parse OK — version={proj.version}  tempo={proj.tempo}  ppq={proj.ppq}")

    try:
        n_patterns = sum(1 for _ in proj.patterns)
    except Exception:
        n_patterns = "?"
    print(f"  Patterns visible to pyflp: {n_patterns}")

    pyflp.save(proj, out_path)
    print(f"  Saved round-trip copy → {out_path}")
    tmp.unlink()
    return True


def run_from_template(template: Path, out_path: Path) -> bool:
    """Parse user's template, add a test pattern, save as a copy."""
    print(f"[Stage 1] Parsing template: {template}")

    try:
        proj = pyflp.parse(template)
    except Exception as e:
        print(f"  FAIL — pyflp.parse() raised: {e}")
        return False

    print(f"  Parse OK — version={proj.version}  tempo={proj.tempo}  ppq={proj.ppq}")

    try:
        ch_count = len(proj.channels)
        print(f"  Channels: {ch_count}")
    except Exception as e:
        print(f"  Channels: (error reading — {e})")

    try:
        pat_count = sum(1 for _ in proj.patterns)
        print(f"  Patterns before edit: {pat_count}")
    except Exception as e:
        print(f"  Patterns: (error reading — {e})")

    print("  Saving copy (no modifications yet — verifying round-trip)...")
    pyflp.save(proj, out_path)
    print(f"  Saved → {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template", type=Path, default=None,
        help="Path to an existing FL Studio .flp to use as the base project.",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output path for the test file (default: next to template or ./spike_output.flp).",
    )
    args = parser.parse_args()

    if args.template:
        out = args.out or args.template.parent / f"{args.template.stem}_spike.flp"
        ok = run_from_template(args.template, out)
    else:
        out = args.out or Path("spike_output.flp")
        ok = run_from_scratch(out)

    if ok:
        print()
        print("=" * 60)
        print("SPIKE RESULT: pyflp round-trip succeeded on Python", sys.version.split()[0])
        print(f"Output file:  {out.resolve()}")
        print()
        print("Next step: open that file in FL Studio 25 and confirm it loads")
        print("without errors. A minimal project with one pattern is expected.")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("SPIKE RESULT: FAILED — see errors above.")
        print("Fallback plan: use multi-track MIDI output + template project.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
