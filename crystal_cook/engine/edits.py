"""
First-class edit operations — the co-producer's vocabulary.

These are library functions, NOT logic buried in generation. Each returns a
new Manifest version (versioning, never destruction) with a one-line,
legible changelog referencing concrete before/after values.

The keep_rhythm / keep_pitches decomposition in regenerate_stem is the most
important primitive (SPEC), so it is implemented at the note level: keeping
rhythm repitches in place; keeping pitches re-times the same pitch multiset.
"""
from __future__ import annotations

import copy
import random

from . import theory
from .manifest import Manifest
from .model import REGISTER, Note, Role, Stem


def _new_version(manifest: Manifest, changelog: str) -> Manifest:
    m = copy.deepcopy(manifest)
    m.parent = manifest.version
    m.version = manifest.version + 1
    m.changelog = changelog
    return m


def _section_indices(manifest: Manifest, section):
    """Resolve a section selector (int index, type name, or None=all)."""
    secs = manifest.song.sections
    if section is None:
        return list(range(len(secs)))
    if isinstance(section, int):
        return [section]
    return [i for i, s in enumerate(secs) if s.type == section]


def set_section_energy(manifest: Manifest, section: int, energy: float) -> Manifest:
    before = manifest.song.sections[section].energy
    m = _new_version(manifest, "")
    m.song.sections[section].energy = round(max(0.0, min(1.0, energy)), 3)
    m.changelog = (f"set {m.song.sections[section].type}[{section}] energy "
                   f"{before} -> {m.song.sections[section].energy}")
    return m


def transpose(manifest: Manifest, role: str, sections, interval: int) -> Manifest:
    idxs = set(_section_indices(manifest, sections))
    lo, hi = REGISTER[Role(role)]
    m = _new_version(manifest, "")
    stem = m.song.stem(role)
    if stem is None:
        m.changelog = f"transpose {role}: no such stem (no-op)"
        return m
    n_moved = 0
    for note in stem.notes:
        if note.section_index in idxs:
            note.pitch = theory.nearest_in_register(note.pitch + interval, lo, hi)
            n_moved += 1
    m.changelog = f"transposed {role} by {interval:+d} semitones across {n_moved} notes"
    return m


def thin_density(manifest: Manifest, role: str, section, factor: float) -> Manifest:
    idxs = set(_section_indices(manifest, section))
    m = _new_version(manifest, "")
    stem = m.song.stem(role)
    if stem is None:
        m.changelog = f"thin {role}: no such stem (no-op)"
        return m
    rng = random.Random(f"{m.song.seed}:thin:{role}:{section}")
    kept, removed = [], 0
    for note in stem.notes:
        if note.section_index in idxs and rng.random() > factor:
            removed += 1
            continue
        kept.append(note)
    before = len(stem.notes)
    stem.notes = kept
    m.changelog = (f"thinned {role} in section {section} by factor {factor}: "
                   f"{before} -> {len(kept)} notes ({removed} removed)")
    return m


def regenerate_stem(manifest: Manifest, role: str, section: int,
                    keep_rhythm: bool = False, keep_pitches: bool = False) -> Manifest:
    m = _new_version(manifest, "")
    stem = m.song.stem(role)
    if stem is None:
        m.changelog = f"regenerate {role}: no such stem (no-op)"
        return m

    sec = m.song.sections[section]
    in_sec = [n for n in stem.notes if n.section_index == section]
    others = [n for n in stem.notes if n.section_index != section]
    if not in_sec:
        m.changelog = f"regenerate {role} section {section}: empty (no-op)"
        return m

    rng = random.Random(f"{m.song.seed}:regen:{role}:{section}:{m.version}")
    lo, hi = REGISTER[Role(role)]
    # Chord tones available in this section (for repitching melodic roles).
    tone_pool = []
    for bar, deg in enumerate(sec.progression):
        tone_pool += [theory.nearest_in_register(p, lo, hi)
                      for p in theory.triad(m.song.key, m.song.scale, deg)]
    tone_pool = sorted(set(tone_pool)) or [lo]

    if keep_rhythm and not keep_pitches:
        for n in in_sec:
            n.pitch = rng.choice(tone_pool)
        desc = "kept rhythm, repitched"
    elif keep_pitches and not keep_rhythm:
        starts = sorted(n.start_beat for n in in_sec)
        rng.shuffle(starts)
        for n, s in zip(in_sec, starts):
            n.start_beat = s
        desc = "kept pitches, re-timed"
    else:
        for n in in_sec:
            n.pitch = rng.choice(tone_pool)
        starts = sorted(n.start_beat for n in in_sec)
        rng.shuffle(starts)
        for n, s in zip(in_sec, starts):
            n.start_beat = s
        desc = "fully regenerated"

    stem.notes = others + in_sec
    stem.notes.sort(key=lambda n: n.start_beat)
    m.changelog = f"regenerate {role} section {section}: {desc} ({len(in_sec)} notes)"
    return m


def swap_progression(manifest: Manifest, section: int, family: str) -> Manifest:
    if family not in theory.PROGRESSION_FAMILIES:
        raise ValueError(f"Unknown progression family: {family}")
    m = _new_version(manifest, "")
    sec = m.song.sections[section]
    base = theory.PROGRESSION_FAMILIES[family]
    before = sec.progression
    sec.progression = [base[b % len(base)] for b in range(sec.length_bars)]
    m.changelog = (f"swapped progression of section {section} to {family} "
                   f"({before} -> {sec.progression})")
    return m


def recast_preset(manifest: Manifest, role: str, vibe: str) -> Manifest:
    """Stage 4 — records intent now; preset library wiring lands in Stage 4."""
    m = _new_version(manifest, "")
    m.cast_presets[role] = {"vibe": vibe, "preset": None}
    m.changelog = f"recast {role} to vibe '{vibe}' (preset selection pending Stage 4)"
    return m
