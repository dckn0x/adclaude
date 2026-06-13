# Stage 1 — PyFLP Spike Findings

**Date:** 2026-06-13
**FL Studio:** 25.2.5.5319 (Windows)
**Python:** 3.11.15
**PyFLP:** 2.2.1

## Result: PASS ✅

PyFLP can produce a `.flp` that FL Studio 25.2.5 opens cleanly. The
round-trip de-risk succeeds; Stage 3 (FLP writer) is viable. No fallback
to MIDI-only output is required.

## Test artifact

`spike_output.flp` — a 141-byte minimal project (title "crystal-cook-spike",
140 BPM, one channel, one pattern "Stage1 Spike" with a single middle-C
note). Opened in FL 25.2.5 without errors; note appeared at the correct
pitch (C5 in FL's octave numbering = MIDI 60 = middle C).

## Bug found and patched: PyFLP 2.2.1 is broken on Python 3.11

`EventEnum(value)` raises `TypeError: <enum 'EventEnum'> has no members
defined` on Python ≥ 3.11. Python 3.11 added a guard in `enum.__new__` that
raises *before* the `_missing_()` hook is called when the enum class has no
**direct** members. `EventEnum` has none — all real members live in
subclasses (`ProjectID`, `ChannelID`, `PatternID`, …). PyFLP's own
`parse()` calls `EventEnum(byte)` on the first event and dies immediately,
so the library cannot parse *any* file under Python 3.11.

**Fix:** `crystal_cook/compat.py` monkey-patches `pyflp.parse` to route the
event-ID lookup through `EventEnum._missing_(value)` directly, bypassing the
3.11 guard. `_missing_()` already does the correct subclass search. Call
`crystal_cook.compat.patch()` before any `pyflp.parse`/`pyflp.save`.

## Ghost-note observation (channel binding)

The minimal file declared one bare channel (no instrument) with a note at
`rack_channel = 0`. FL substituted a default Sampler and focused the piano
roll on it; our note bound to a different rack slot and rendered as a
**ghost note** (a note belonging to a non-focused channel). Drawing a note
over it triggered the focused Sampler, not the ghost's channel — hence the
"plays something different" behavior.

**Stage 3 implication:** never hardcode `note.rack_channel`. Parse the
template, match channels by role name, and use each channel's real rack
index. Note targets must be fully-formed instrument channels — guaranteed
by the template.

## Reproduce

```bash
# From scratch (no template needed):
python -m crystal_cook.spike.stage1_pyflp_test

# Against a real template:
python -m crystal_cook.spike.stage1_pyflp_test --template /path/to/template.flp
```
