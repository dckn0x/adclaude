"""
Stem generation: turn the arrangement + profile into role-tagged note
sequences. All musical decisions are seeded and reproducible.

Rules encoded here (from SPEC):
- Diatonic progressions voiced for keys/pads register (chaos=0 baseline).
- LEAD sits on the chord bed; COUNTER is call-and-response (fills LEAD rests).
- BASS_808 follows chord roots; overlapping notes where glides are intended.
- Drums per the genre profile's rhythm character; swing per profile.
- Transition logic: bar-before-hook fill/mute, hat rolls into downbeats.
- Verse 2 derives from verse 1 (fragment reuse + rhythmic displacement).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import theory
from .model import (
    DRUM_ROLES, MELODIC_ROLES, REGISTER, Note, Role, Section, SectionType, Stem,
)
from .profile import ResolvedProfile
from .rng import CookRandom

BEATS_PER_BAR = 4.0

# Fixed drum trigger pitches.
KICK_PITCH = 36
SNARE_PITCH = 38
HAT_CLOSED = 42
HAT_OPEN = 46
PERC_PITCH = 37


@dataclass
class GenContext:
    key: str
    scale: str
    profile: ResolvedProfile
    rng: CookRandom
    chaos: float
    sections: list[Section]

    def section_start_beat(self, idx: int) -> float:
        return sum(s.length_bars for s in self.sections[:idx]) * BEATS_PER_BAR

    def density_for(self, role: str, energy: float) -> float:
        d = self.profile.density(role)
        return d["low"] + (d["high"] - d["low"]) * energy

    def velocity(self, energy: float, stream: str, lo: int = 60, hi: int = 112) -> int:
        base = lo + (hi - lo) * energy
        jitter = self.rng.stream(stream).uniform(-6, 6) * (1 + self.chaos)
        return max(1, min(127, int(round(base + jitter))))

    def swing_offset(self, role: str, slot_idx: int, division: float) -> float:
        if role not in self.profile.swing_roles():
            return 0.0
        if slot_idx % 2 == 1:  # offbeat
            return self.profile.swing_amount() * division
        return 0.0

    def humanize(self, stream: str) -> float:
        """Small timing jitter in beats, grows with chaos."""
        amt = 0.005 + 0.02 * self.chaos
        return self.rng.stream(stream).uniform(-amt, amt)


# ── Melodic roles ─────────────────────────────────────────────────────────────

def gen_chords(ctx: GenContext) -> Stem:
    stem = Stem(role=Role.CHORDS.value)
    lo, hi = REGISTER[Role.CHORDS]
    r = ctx.rng.stream("chords")
    for si, sec in enumerate(ctx.sections):
        if Role.CHORDS.value not in sec.active_roles:
            continue
        start = ctx.section_start_beat(si)
        use_seventh = ctx.chaos > 0.3 and r.random() < (ctx.chaos * 0.5)
        for bar in range(sec.length_bars):
            degree = sec.progression[bar % len(sec.progression)]
            tones = theory.seventh(ctx.key, ctx.scale, degree) if use_seventh \
                else theory.triad(ctx.key, ctx.scale, degree)
            bar_start = start + bar * BEATS_PER_BAR
            vel = ctx.velocity(sec.energy, "chords", 50, 95)
            for t in tones:
                pitch = theory.nearest_in_register(t, lo, hi)
                stem.notes.append(Note(
                    start_beat=round(bar_start, 4),
                    duration_beats=BEATS_PER_BAR * 0.95,
                    pitch=pitch,
                    velocity=vel,
                    section_index=si,
                ))
    return stem


def gen_bass(ctx: GenContext) -> Stem:
    """808 follows chord roots; overlapping notes signal glide to the synth."""
    stem = Stem(role=Role.BASS_808.value)
    lo, hi = REGISTER[Role.BASS_808]
    for si, sec in enumerate(ctx.sections):
        if Role.BASS_808.value not in sec.active_roles:
            continue
        start = ctx.section_start_beat(si)
        roots = []
        for bar in range(sec.length_bars):
            degree = sec.progression[bar % len(sec.progression)]
            root = theory.nearest_in_register(
                theory.chord_root_pitch(ctx.key, ctx.scale, degree, octave=2), lo, hi
            )
            roots.append(root)
        for bar in range(sec.length_bars):
            bar_start = start + bar * BEATS_PER_BAR
            vel = ctx.velocity(sec.energy, "bass", 70, 118)
            # Overlap into the next bar when the root changes -> glide.
            next_changes = (bar + 1 < sec.length_bars) and (roots[bar] != roots[bar + 1])
            dur = BEATS_PER_BAR + (0.12 if next_changes else -0.05)
            stem.notes.append(Note(
                start_beat=round(bar_start, 4),
                duration_beats=round(dur, 4),
                pitch=roots[bar],
                velocity=vel,
                section_index=si,
            ))
    return stem


def _bar_chord_tones(ctx: GenContext, sec: Section, bar: int, lo: int, hi: int) -> list[int]:
    degree = sec.progression[bar % len(sec.progression)]
    tones = theory.triad(ctx.key, ctx.scale, degree)
    return [theory.nearest_in_register(t, lo, hi) for t in tones]


def gen_lead(ctx: GenContext) -> tuple[Stem, dict[int, dict[int, set[int]]]]:
    """
    LEAD melody on a 8th-note grid. Returns the stem plus a rest map:
    rest_map[section_index][bar] = set of free slot indices (for COUNTER).
    """
    stem = Stem(role=Role.LEAD.value)
    lo, hi = REGISTER[Role.LEAD]
    division = 0.5  # 8th notes
    slots_per_bar = int(BEATS_PER_BAR / division)  # 8
    r = ctx.rng.stream("lead")
    rest_map: dict[int, dict[int, set[int]]] = {}

    for si, sec in enumerate(ctx.sections):
        rest_map[si] = {}
        if Role.LEAD.value not in sec.active_roles:
            for bar in range(sec.length_bars):
                rest_map[si][bar] = set(range(slots_per_bar))
            continue
        start = ctx.section_start_beat(si)
        density = ctx.density_for(Role.LEAD.value, sec.energy)
        prev_pitch = None
        for bar in range(sec.length_bars):
            tones = _bar_chord_tones(ctx, sec, bar, lo, hi)
            # Downbeats favored: weight slot selection.
            n_active = max(1, int(round(density * slots_per_bar)))
            weights = [3 if s % 2 == 0 else 1 for s in range(slots_per_bar)]
            chosen = set(r.choices(range(slots_per_bar), weights=weights, k=n_active))
            free = set(range(slots_per_bar)) - chosen
            rest_map[si][bar] = free
            bar_start = start + bar * BEATS_PER_BAR
            for slot in sorted(chosen):
                # Mostly chord tones; passing scale tones under more chaos.
                if prev_pitch is not None and r.random() < 0.4 + ctx.chaos * 0.2:
                    step = r.choice([-2, -1, 1, 2])
                    pitch = theory.nearest_in_register(prev_pitch + step, lo, hi)
                    if not theory.is_in_scale(pitch, ctx.key, ctx.scale):
                        pitch = r.choice(tones)
                else:
                    pitch = r.choice(tones)
                prev_pitch = pitch
                onset = bar_start + slot * division \
                    + ctx.swing_offset(Role.LEAD.value, slot, division) \
                    + ctx.humanize("lead_h")
                stem.notes.append(Note(
                    start_beat=round(onset, 4),
                    duration_beats=division * 0.9,
                    pitch=pitch,
                    velocity=ctx.velocity(sec.energy, "lead", 60, 108),
                    section_index=si,
                ))
    return stem, rest_map


def gen_counter(ctx: GenContext, rest_map: dict[int, dict[int, set[int]]]) -> Stem:
    """COUNTER fills LEAD's rests (call-and-response), in a lower register."""
    stem = Stem(role=Role.COUNTER.value)
    lo, hi = REGISTER[Role.COUNTER]
    division = 0.5
    r = ctx.rng.stream("counter")
    for si, sec in enumerate(ctx.sections):
        if Role.COUNTER.value not in sec.active_roles:
            continue
        start = ctx.section_start_beat(si)
        density = ctx.density_for(Role.COUNTER.value, sec.energy)
        for bar in range(sec.length_bars):
            free = sorted(rest_map.get(si, {}).get(bar, set()))
            if not free:
                continue
            n = max(0, int(round(density * len(free))))
            chosen = r.sample(free, min(n, len(free))) if n else []
            tones = _bar_chord_tones(ctx, sec, bar, lo, hi)
            bar_start = start + bar * BEATS_PER_BAR
            for slot in sorted(chosen):
                pitch = r.choice(tones)
                onset = bar_start + slot * division \
                    + ctx.swing_offset(Role.COUNTER.value, slot, division) \
                    + ctx.humanize("counter_h")
                stem.notes.append(Note(
                    start_beat=round(onset, 4),
                    duration_beats=division * 0.85,
                    pitch=pitch,
                    velocity=ctx.velocity(sec.energy, "counter", 50, 95),
                    section_index=si,
                ))
    return stem


# ── Drum roles ──────────────────────────────────────────────────────────────

def gen_kick(ctx: GenContext) -> Stem:
    stem = Stem(role=Role.KICK.value)
    r = ctx.rng.stream("kick")
    for si, sec in enumerate(ctx.sections):
        if Role.KICK.value not in sec.active_roles:
            continue
        rhythm = ctx.profile.rhythm(Role.KICK.value)
        density = float(rhythm.get("density", 0.4))
        sync = float(rhythm.get("syncopation", 0.5))
        start = ctx.section_start_beat(si)
        for bar in range(sec.length_bars):
            bar_start = start + bar * BEATS_PER_BAR
            # Beat 1 almost always.
            if r.random() < 0.9:
                _add_drum(ctx, stem, bar_start, KICK_PITCH, sec, si, "kick")
            # Syncopated hits on the 16th grid.
            for slot in range(1, 16):
                p = density * (sync if slot % 4 != 0 else 0.4)
                if r.random() < p * 0.3:
                    onset = bar_start + slot * 0.25 \
                        + ctx.swing_offset(Role.KICK.value, slot, 0.25)
                    _add_drum(ctx, stem, onset, KICK_PITCH, sec, si, "kick")
    return stem


def gen_snare(ctx: GenContext) -> Stem:
    stem = Stem(role=Role.SNARE.value)
    r = ctx.rng.stream("snare")
    for si, sec in enumerate(ctx.sections):
        if Role.SNARE.value not in sec.active_roles:
            continue
        rhythm = ctx.profile.rhythm(Role.SNARE.value)
        pattern = rhythm.get("pattern", "backbeat")
        ghost = float(rhythm.get("ghost_notes", 0.1))
        start = ctx.section_start_beat(si)
        for bar in range(sec.length_bars):
            bar_start = start + bar * BEATS_PER_BAR
            hits = [2.0] if pattern == "halftime" else [1.0, 3.0]  # beats (0-indexed)
            for b in hits:
                _add_drum(ctx, stem, bar_start + b, SNARE_PITCH, sec, si, "snare")
            # Ghost notes on the 16th grid.
            for slot in range(16):
                if slot % 4 == 0:
                    continue
                if r.random() < ghost * 0.25:
                    onset = bar_start + slot * 0.25 \
                        + ctx.swing_offset(Role.SNARE.value, slot, 0.25)
                    _add_drum(ctx, stem, onset, SNARE_PITCH + 1, sec, si, "snare",
                              vel_scale=0.4)
    return stem


def gen_hats(ctx: GenContext) -> Stem:
    stem = Stem(role=Role.HATS.value)
    r = ctx.rng.stream("hats")
    for si, sec in enumerate(ctx.sections):
        if Role.HATS.value not in sec.active_roles:
            continue
        rhythm = ctx.profile.rhythm(Role.HATS.value)
        division = float(rhythm.get("base_division", 0.5))
        roll_freq = float(rhythm.get("roll_frequency", 0.2))
        roll_divs = rhythm.get("roll_divisions", [0.25])
        slots_per_bar = int(round(BEATS_PER_BAR / division))
        start = ctx.section_start_beat(si)
        for bar in range(sec.length_bars):
            bar_start = start + bar * BEATS_PER_BAR
            for slot in range(slots_per_bar):
                onset = bar_start + slot * division \
                    + ctx.swing_offset(Role.HATS.value, slot, division) \
                    + ctx.humanize("hats_h")
                _add_drum(ctx, stem, onset, HAT_CLOSED, sec, si, "hats",
                          vel_scale=0.7 if slot % 2 else 0.85)
            # Hat roll — frequency scales with section energy.
            if r.random() < roll_freq * (0.5 + sec.energy):
                rdiv = r.choice(roll_divs)
                roll_start = bar_start + BEATS_PER_BAR - r.choice([1.0, 0.5])
                t = roll_start
                while t < bar_start + BEATS_PER_BAR - 1e-6:
                    _add_drum(ctx, stem, t, HAT_CLOSED, sec, si, "hats", vel_scale=0.6)
                    t += rdiv
    return stem


def gen_perc(ctx: GenContext) -> Stem:
    stem = Stem(role=Role.PERC.value)
    r = ctx.rng.stream("perc")
    for si, sec in enumerate(ctx.sections):
        if Role.PERC.value not in sec.active_roles:
            continue
        rhythm = ctx.profile.rhythm(Role.PERC.value)
        density = float(rhythm.get("density", 0.25))
        start = ctx.section_start_beat(si)
        for bar in range(sec.length_bars):
            bar_start = start + bar * BEATS_PER_BAR
            for slot in range(8):
                if r.random() < density * 0.3:
                    onset = bar_start + slot * 0.5 \
                        + ctx.swing_offset(Role.PERC.value, slot, 0.5)
                    _add_drum(ctx, stem, onset, PERC_PITCH, sec, si, "perc",
                              vel_scale=0.6)
    return stem


def _add_drum(ctx: GenContext, stem: Stem, onset: float, pitch: int,
              sec: Section, si: int, stream: str, vel_scale: float = 1.0):
    lo, hi = REGISTER[Role[stem.role]]
    pitch = max(lo, min(hi, pitch))
    vel = int(round(ctx.velocity(sec.energy, stream, 60, 115) * vel_scale))
    vel = max(1, min(127, vel))
    stem.notes.append(Note(
        start_beat=round(onset, 4),
        duration_beats=0.12,
        pitch=pitch,
        velocity=vel,
        section_index=si,
    ))


# ── Transition pass ───────────────────────────────────────────────────────────

def apply_transitions(ctx: GenContext, stems: dict[str, Stem]) -> None:
    """
    Bar-before-hook treatment: hat roll into the downbeat, and mute the bass
    on the final beat so the hook's 808 lands fresh. Fill density rises with
    the target hook's energy.
    """
    hats = stems.get(Role.HATS.value)
    bass = stems.get(Role.BASS_808.value)
    for si in range(len(ctx.sections) - 1):
        nxt = ctx.sections[si + 1]
        if nxt.type != SectionType.HOOK.value:
            continue
        sec = ctx.sections[si]
        sec_start = ctx.section_start_beat(si)
        last_bar_start = sec_start + (sec.length_bars - 1) * BEATS_PER_BAR
        # Hat roll into the downbeat (intensity from target energy).
        if hats is not None and Role.HATS.value in sec.active_roles:
            rdiv = 0.125 if nxt.energy > 0.7 else 0.25
            t = last_bar_start + 2.0
            while t < last_bar_start + BEATS_PER_BAR - 1e-6:
                _add_drum(ctx, hats, t, HAT_CLOSED, sec, si, "fill", vel_scale=0.7)
                t += rdiv
        # Mute bass on the final beat before the hook.
        if bass is not None:
            cutoff = last_bar_start + 3.0
            for n in bass.notes:
                if n.section_index == si and n.start_beat + n.duration_beats > cutoff \
                        and n.start_beat < cutoff:
                    n.duration_beats = max(0.1, cutoff - n.start_beat)


# ── Verse-2 derivation ────────────────────────────────────────────────────────

def apply_verse_derivation(ctx: GenContext, stems: dict[str, Stem]) -> None:
    """
    Verse 2+ derives from verse 1 via melodic fragment reuse + rhythmic
    displacement — never a verbatim copy. We reuse the source verse's pitches
    (shared contour) but displace timing and drop a fragment, so the result is
    recognizably related yet distinct.
    """
    r = ctx.rng.stream("verse_derive")
    for si, sec in enumerate(ctx.sections):
        if sec.variation_source is None:
            continue
        src = sec.variation_source
        delta = (ctx.section_start_beat(si) - ctx.section_start_beat(src))
        sec_len_beats = sec.length_bars * BEATS_PER_BAR
        sec_start = ctx.section_start_beat(si)
        for role in (Role.LEAD.value, Role.COUNTER.value):
            stem = stems.get(role)
            if stem is None:
                continue
            src_notes = [n for n in stem.notes if n.section_index == src]
            if not src_notes:
                continue
            # Drop everything currently in the derived section.
            stem.notes = [n for n in stem.notes if n.section_index != si]
            for n in src_notes:
                if r.random() < 0.25:        # fragment reuse: omit ~1/4 of notes
                    continue
                new_start = n.start_beat + delta
                if r.random() < 0.5:         # rhythmic displacement on ~half
                    new_start += r.choice([-0.25, 0.25, 0.125])
                # Keep within the derived section's time window.
                if new_start < sec_start or new_start >= sec_start + sec_len_beats:
                    continue
                stem.notes.append(Note(
                    start_beat=round(new_start, 4),
                    duration_beats=n.duration_beats,
                    pitch=n.pitch,
                    velocity=n.velocity,
                    section_index=si,
                ))
            stem.notes.sort(key=lambda x: x.start_beat)


# ── Orchestration ─────────────────────────────────────────────────────────────

def generate_all_stems(ctx: GenContext) -> list[Stem]:
    stems: dict[str, Stem] = {}
    stems[Role.CHORDS.value] = gen_chords(ctx)
    stems[Role.BASS_808.value] = gen_bass(ctx)
    lead, rest_map = gen_lead(ctx)
    stems[Role.LEAD.value] = lead
    stems[Role.COUNTER.value] = gen_counter(ctx, rest_map)
    stems[Role.KICK.value] = gen_kick(ctx)
    stems[Role.SNARE.value] = gen_snare(ctx)
    stems[Role.HATS.value] = gen_hats(ctx)
    stems[Role.PERC.value] = gen_perc(ctx)

    apply_verse_derivation(ctx, stems)
    apply_transitions(ctx, stems)

    # Return only stems that actually have notes, in canonical role order.
    order = [r.value for r in Role]
    return [stems[r] for r in order if r in stems and stems[r].notes]
