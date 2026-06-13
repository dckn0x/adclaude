"""
Arrangement: song-form grammar -> sections with energy curve, progressions,
role activation, and variation sources.

Default form (overridable via --form):
  INTRO(8) -> VERSE(8) -> HOOK(8) -> VERSE(8) -> HOOK(8)
  -> BREAKDOWN(4-8) -> HOOK(8) -> OUTRO(4)
"""
from __future__ import annotations

import re

from .model import Role, Section, SectionType
from .profile import ResolvedProfile
from .rng import CookRandom

DEFAULT_FORM = "INTRO(8) VERSE(8) HOOK(8) VERSE(8) HOOK(8) BREAKDOWN(8) HOOK(8) OUTRO(4)"

# Baseline energy per section type (0..1). The energy curve drives both
# discrete decisions and continuous gesture amplitudes.
ENERGY_BASELINE = {
    SectionType.INTRO: 0.30,
    SectionType.VERSE: 0.50,
    SectionType.HOOK: 0.85,
    SectionType.BRIDGE: 0.60,
    SectionType.BREAKDOWN: 0.22,
    SectionType.OUTRO: 0.32,
}

_FORM_TOKEN = re.compile(r"([A-Z]+)\((\d+)\)")


def parse_form(form: str) -> list[tuple[str, int]]:
    """Parse a form string like 'INTRO(8) VERSE(8)' -> [('INTRO',8),...]."""
    tokens = _FORM_TOKEN.findall(form)
    if not tokens:
        raise ValueError(f"Could not parse form string: {form!r}")
    out = []
    for name, bars in tokens:
        if name not in SectionType.__members__:
            raise ValueError(f"Unknown section type {name!r} in form")
        out.append((name, int(bars)))
    return out


def _sample_active_roles(profile: ResolvedProfile, rng: CookRandom) -> set[str]:
    """Sample the cook-level active role set from activation weights."""
    r = rng.stream("activation")
    active = set()
    for role in Role:
        if role == Role.CHOPS:
            continue  # Stage 8 only
        w = profile.activation_weight(role.value)
        if r.random() < w:
            active.add(role.value)
    # Guarantee at least chords + some low end so a cook is never empty.
    active.add(Role.CHORDS.value)
    if Role.BASS_808.value not in active and Role.KICK.value not in active:
        active.add(Role.BASS_808.value)
    return active


def _section_active_roles(stype: SectionType, energy: float, cook_active: set[str]) -> list[str]:
    """Thin the active set for low-energy sections; full set for hooks."""
    roles = set(cook_active)
    if stype == SectionType.INTRO:
        # Strip heavy drums; keep harmonic bed and maybe perc/hats.
        roles -= {Role.KICK.value, Role.SNARE.value}
        if energy < 0.35:
            roles -= {Role.BASS_808.value}
    elif stype == SectionType.BREAKDOWN:
        # Pull the rhythm section back so the next hook lands huge.
        roles -= {Role.KICK.value, Role.HATS.value, Role.PERC.value}
    elif stype == SectionType.OUTRO:
        roles -= {Role.HATS.value, Role.PERC.value}
    # HOOK / VERSE / BRIDGE keep the full active set.
    # Preserve canonical role order.
    order = [r.value for r in Role]
    return [r for r in order if r in roles]


def _choose_progression(profile: ResolvedProfile, rng: CookRandom) -> list[int]:
    """Pick a progression family weighted by profile, return scale-degree list."""
    from .theory import PROGRESSION_FAMILIES
    weights = profile.progression_weights()
    fams = [f for f in weights if f in PROGRESSION_FAMILIES]
    if not fams:
        fams = ["i-VI-III-VII"]
        weights = {"i-VI-III-VII": 1.0}
    r = rng.stream("progression")
    chosen = r.choices(fams, weights=[weights[f] for f in fams], k=1)[0]
    return list(PROGRESSION_FAMILIES[chosen])


def _maybe_odd_length(bars: int, chaos: float, rng) -> int:
    """Under chaos, occasionally shift a section to an odd bar count."""
    if chaos >= 0.4 and rng.random() < (chaos - 0.3):
        return rng.choice([3, 5, 7])
    return bars


def build_sections(
    profile: ResolvedProfile,
    rng: CookRandom,
    chaos: float,
    form: str | None = None,
) -> list[Section]:
    form = form or DEFAULT_FORM
    spec = parse_form(form)

    cook_active = _sample_active_roles(profile, rng)
    base_prog = _choose_progression(profile, rng)
    energy_rng = rng.stream("energy")
    length_rng = rng.stream("length")

    sections: list[Section] = []
    first_verse_idx: int | None = None

    for i, (name, bars) in enumerate(spec):
        stype = SectionType[name]
        bars = _maybe_odd_length(bars, chaos, length_rng)

        # Energy = baseline + small seeded jitter, clamped.
        energy = ENERGY_BASELINE[stype] + energy_rng.uniform(-0.05, 0.05)
        energy = max(0.0, min(1.0, energy))

        active = _section_active_roles(stype, energy, cook_active)

        # Progression: cycle the family to fill the bar count (one chord/bar).
        progression = [base_prog[b % len(base_prog)] for b in range(bars)]

        section = Section(
            type=stype.value,
            length_bars=bars,
            energy=round(energy, 3),
            active_roles=active,
            progression=progression,
        )

        # Verse 2+ derives from verse 1 (fragment reuse + rhythmic displacement).
        if stype == SectionType.VERSE:
            if first_verse_idx is None:
                first_verse_idx = i
            else:
                section.variation_source = first_verse_idx
                section.variation_ops = ["fragment_reuse", "rhythmic_displacement"]

        sections.append(section)

    return sections
