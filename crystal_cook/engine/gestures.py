"""
Gesture engine: stamp parametric automation curves at section boundaries.

Signature moves (from SPEC, "elegant out of the box"):
- SPACE swells through the bar before each hook, then cuts dry on the downbeat.
- CUTOFF starts closed in intros/breakdowns, opens across the transition.
- WIDTH: narrow verses, wide hooks, mono breakdown.
- DRIVE on BASS_808 scales with section energy.
- Drums NEVER receive SPACE swells.
- COUNTER gets one slow drift per section.
- Ending: all sends killed (dry hit) OR one note rings into max SPACE. Coin-flip.
"""
from __future__ import annotations

from . import macros
from .model import (
    DRUM_ROLES, Gesture, GestureShape, Role, Section, SectionType, Stem,
)
from .stems import GenContext, BEATS_PER_BAR

# Per-section-type WIDTH targets (0-127).
WIDTH_TARGET = {
    SectionType.INTRO: 60,
    SectionType.VERSE: 45,
    SectionType.HOOK: 110,
    SectionType.BRIDGE: 70,
    SectionType.BREAKDOWN: 0,   # mono — so the hook lands huge
    SectionType.OUTRO: 70,
}

# CUTOFF baseline per section type (0-127).
CUTOFF_BASELINE = {
    SectionType.INTRO: 35,
    SectionType.VERSE: 85,
    SectionType.HOOK: 110,
    SectionType.BRIDGE: 80,
    SectionType.BREAKDOWN: 30,
    SectionType.OUTRO: 60,
}

MELODIC = (Role.CHORDS.value, Role.LEAD.value, Role.COUNTER.value, Role.BASS_808.value)


def _stem(stems: dict[str, Stem], role: str) -> Stem | None:
    return stems.get(role)


def _present_melodic(stems: dict[str, Stem]) -> list[str]:
    return [r for r in MELODIC if r in stems]


def generate_gestures(ctx: GenContext, stems: dict[str, Stem],
                      ending_mode: str) -> None:
    """Mutates each stem's .gestures list in place."""
    space_amp = ctx.profile.gesture("space_into_hook")
    cutoff_amp = ctx.profile.gesture("cutoff_open")
    width_amp = ctx.profile.gesture("width_spread")
    drive_amp = ctx.profile.gesture("drive_on_808")

    n = len(ctx.sections)

    for si, sec in enumerate(ctx.sections):
        stype = SectionType(sec.type)
        sec_start = ctx.section_start_beat(si)
        sec_len_beats = sec.length_bars * BEATS_PER_BAR
        sec_end = sec_start + sec_len_beats

        # ── WIDTH: step to the section target on each melodic role ──
        width_val = int(round(WIDTH_TARGET[stype] * width_amp))
        width_val = max(0, min(127, width_val))
        for role in _present_melodic(stems):
            stems[role].gestures.append(Gesture(
                target_cc=macros.WIDTH, role=role,
                start_beat=round(sec_start, 4), end_beat=round(sec_start, 4),
                shape=GestureShape.CUT.value,
                value_start=width_val, value_end=width_val,
            ))

        # ── CUTOFF: open across intros/breakdowns; otherwise hold baseline ──
        base = CUTOFF_BASELINE[stype]
        if stype in (SectionType.INTRO, SectionType.BREAKDOWN):
            for role in _present_melodic(stems):
                stems[role].gestures.append(Gesture(
                    target_cc=macros.CUTOFF, role=role,
                    start_beat=round(sec_start, 4), end_beat=round(sec_end, 4),
                    shape=GestureShape.RAMP.value,
                    value_start=base,
                    value_end=min(127, int(round(base + 70 * cutoff_amp))),
                ))
        else:
            for role in _present_melodic(stems):
                stems[role].gestures.append(Gesture(
                    target_cc=macros.CUTOFF, role=role,
                    start_beat=round(sec_start, 4), end_beat=round(sec_start, 4),
                    shape=GestureShape.CUT.value,
                    value_start=base, value_end=base,
                ))

        # ── DRIVE on BASS_808 scales with section energy ──
        if Role.BASS_808.value in stems:
            drive = int(round(sec.energy * 110 * drive_amp))
            drive = max(0, min(127, drive))
            stems[Role.BASS_808.value].gestures.append(Gesture(
                target_cc=macros.DRIVE, role=Role.BASS_808.value,
                start_beat=round(sec_start, 4), end_beat=round(sec_start, 4),
                shape=GestureShape.CUT.value,
                value_start=drive, value_end=drive,
            ))

        # ── COUNTER: one slow drift per section so static passages breathe ──
        if Role.COUNTER.value in stems and Role.COUNTER.value in sec.active_roles:
            r = ctx.rng.stream("drift")
            lo = 40 + int(r.uniform(-10, 10))
            hi = lo + 30 + int(r.uniform(-10, 20))
            stems[Role.COUNTER.value].gestures.append(Gesture(
                target_cc=macros.CUTOFF, role=Role.COUNTER.value,
                start_beat=round(sec_start, 4), end_beat=round(sec_end, 4),
                shape=GestureShape.DRIFT.value,
                value_start=max(0, lo), value_end=min(127, hi),
            ))

        # ── SPACE swell into the next hook, then cut dry on the downbeat ──
        nxt = ctx.sections[si + 1] if si + 1 < n else None
        if nxt is not None and nxt.type == SectionType.HOOK.value:
            swell_start = sec_end - BEATS_PER_BAR  # last bar
            peak = int(round(110 * space_amp))
            for role in _present_melodic(stems):
                if role in DRUM_ROLES:  # belt-and-suspenders; melodic only anyway
                    continue
                stems[role].gestures.append(Gesture(
                    target_cc=macros.SPACE, role=role,
                    start_beat=round(swell_start, 4), end_beat=round(sec_end, 4),
                    shape=GestureShape.SWELL.value,
                    value_start=15, value_end=max(0, min(127, peak)),
                ))
                # Cut dry exactly on the hook downbeat.
                stems[role].gestures.append(Gesture(
                    target_cc=macros.SPACE, role=role,
                    start_beat=round(sec_end, 4), end_beat=round(sec_end, 4),
                    shape=GestureShape.CUT.value,
                    value_start=5, value_end=5,
                ))

    # ── Ending: coin-flip per cook ──
    last_end = ctx.section_start_beat(n - 1) + ctx.sections[n - 1].length_bars * BEATS_PER_BAR
    if ending_mode == "dry":
        for role in _present_melodic(stems):
            stems[role].gestures.append(Gesture(
                target_cc=macros.SPACE, role=role,
                start_beat=round(last_end - 1.0, 4), end_beat=round(last_end, 4),
                shape=GestureShape.CUT.value, value_start=0, value_end=0,
            ))
    else:  # "ring"
        for role in _present_melodic(stems):
            stems[role].gestures.append(Gesture(
                target_cc=macros.SPACE, role=role,
                start_beat=round(last_end - BEATS_PER_BAR, 4), end_beat=round(last_end, 4),
                shape=GestureShape.SWELL.value, value_start=40, value_end=127,
            ))
