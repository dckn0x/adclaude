"""
Core data model for CRYSTAL COOK.

Everything here is plain dataclasses designed to serialize cleanly to/from
the cook.json manifest. The manifest IS the beat: these structures fully
determine the output, and re-rendering from them is deterministic.

Conventions:
- Time is measured in BEATS (float), absolute from song start. 4 beats = 1 bar (4/4).
- Pitch is MIDI note number (0-127). Middle C = 60.
- CC values are 0-127.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Roles ─────────────────────────────────────────────────────────────────────

class Role(str, enum.Enum):
    CHORDS = "CHORDS"
    LEAD = "LEAD"
    COUNTER = "COUNTER"
    BASS_808 = "BASS_808"
    KICK = "KICK"
    SNARE = "SNARE"
    HATS = "HATS"
    PERC = "PERC"
    CHOPS = "CHOPS"  # Stage 8


MELODIC_ROLES = (Role.CHORDS, Role.LEAD, Role.COUNTER, Role.BASS_808)
DRUM_ROLES = (Role.KICK, Role.SNARE, Role.HATS, Role.PERC)


# Register bounds (inclusive MIDI range) per role. Invariant: a role never
# writes notes outside its register. Drums use fixed trigger pitches.
REGISTER: dict[Role, tuple[int, int]] = {
    Role.CHORDS: (48, 72),    # C3 - C5
    Role.LEAD: (67, 91),      # G4 - G6
    Role.COUNTER: (60, 84),   # C4 - C6
    Role.BASS_808: (24, 48),  # C1 - C3
    Role.KICK: (36, 36),      # C2
    Role.SNARE: (38, 40),     # D2 - E2
    Role.HATS: (42, 46),      # F#2 - A#2 (closed/open)
    Role.PERC: (37, 39),      # C#2 - D#2
    Role.CHOPS: (24, 96),     # wide — slice triggers
}


# ── Section types ───────────────────────────────────────────────────────────

class SectionType(str, enum.Enum):
    INTRO = "INTRO"
    VERSE = "VERSE"
    HOOK = "HOOK"
    BRIDGE = "BRIDGE"
    BREAKDOWN = "BREAKDOWN"
    OUTRO = "OUTRO"


class GestureShape(str, enum.Enum):
    RAMP = "ramp"      # linear start -> end
    SWELL = "swell"    # rise then the value holds (used for SPACE into hook)
    CUT = "cut"        # instant drop to end value
    DRIFT = "drift"    # slow gentle wander


# ── Leaf structures ───────────────────────────────────────────────────────────

@dataclass
class Note:
    """A single note event, positioned absolutely in beats from song start."""
    start_beat: float
    duration_beats: float
    pitch: int           # MIDI note number
    velocity: int        # 1-127
    section_index: int   # which section this note belongs to (for edits)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Note":
        return cls(**d)


@dataclass
class Gesture:
    """A parametric automation curve stamped on a target macro CC."""
    target_cc: int           # see macros.py (SPACE/CUTOFF/WIDTH/DRIVE)
    role: str                # role name the gesture applies to, or "MASTER"
    start_beat: float
    end_beat: float
    shape: str               # GestureShape value
    value_start: int         # 0-127
    value_end: int           # 0-127

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Gesture":
        return cls(**d)


@dataclass
class Stem:
    """Role-tagged note sequence plus the gestures that target it."""
    role: str                            # Role value
    notes: list[Note] = field(default_factory=list)
    gestures: list[Gesture] = field(default_factory=list)

    def notes_in_section(self, section_index: int) -> list[Note]:
        return [n for n in self.notes if n.section_index == section_index]

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "notes": [n.to_dict() for n in self.notes],
            "gestures": [g.to_dict() for g in self.gestures],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Stem":
        return cls(
            role=d["role"],
            notes=[Note.from_dict(n) for n in d.get("notes", [])],
            gestures=[Gesture.from_dict(g) for g in d.get("gestures", [])],
        )


@dataclass
class SectionRef:
    """Points at the section a derived section was built from."""
    section_index: int


@dataclass
class Section:
    type: str                                  # SectionType value
    length_bars: int                           # 4 or 8 (odd lengths under chaos)
    energy: float                              # 0.0 - 1.0
    active_roles: list[str] = field(default_factory=list)
    variation_source: Optional[int] = None     # index of source section, or None (fresh)
    variation_ops: list[str] = field(default_factory=list)
    progression: list[int] = field(default_factory=list)  # scale-degree indices per chord

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Section":
        return cls(**d)


@dataclass
class Song:
    key: str                  # e.g. "F#"
    scale: str                # e.g. "minor"
    bpm: float
    seed: int
    chaos: float
    genre_spec: str           # original --genre string (e.g. "trap" or "trap:0.6+boombap:0.4")
    global_swing: float
    sections: list[Section] = field(default_factory=list)
    stems: list[Stem] = field(default_factory=list)

    def section_bar_offset(self, index: int) -> int:
        """Bar at which a section begins."""
        return sum(s.length_bars for s in self.sections[:index])

    def section_beat_range(self, index: int) -> tuple[float, float]:
        start_bar = self.section_bar_offset(index)
        start_beat = start_bar * 4.0
        end_beat = start_beat + self.sections[index].length_bars * 4.0
        return start_beat, end_beat

    def total_bars(self) -> int:
        return sum(s.length_bars for s in self.sections)

    def stem(self, role: str) -> Optional[Stem]:
        for s in self.stems:
            if s.role == role:
                return s
        return None
