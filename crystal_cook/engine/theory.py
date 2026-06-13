"""
Music theory primitives: notes, scales, diatonic chords, progression families.

Chaos=0 baseline is strictly diatonic. Borrowed chords and looser voicing are
introduced by the chaos knob (handled in stems.py / arrange.py), not here.
"""
from __future__ import annotations

# Pitch-class index for each note name. Sharps and flats both supported.
NOTE_TO_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4,
    "E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
    "A#": 10, "Bb": 10, "B": 11, "Cb": 11, "B#": 0,
}

PC_TO_NOTE = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
              6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}

# Scale interval patterns (semitones from root).
SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],            # natural minor / aeolian
    "major": [0, 2, 4, 5, 7, 9, 11],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
}

# Progression families as 0-indexed scale degrees (one per chord).
# Defined for minor; the dark/moody families the spec favors come first.
PROGRESSION_FAMILIES = {
    "i-VI-III-VII": [0, 5, 2, 6],     # signature dark family
    "i-III-VII-VI": [0, 2, 6, 5],
    "i-VII-VI-VII": [0, 6, 5, 6],
    "i-iv-v": [0, 3, 4],
    "i-v-VI-iv": [0, 4, 5, 3],
    "i-iv-VII-III": [0, 3, 6, 2],
    "i-VI-iv-v": [0, 5, 3, 4],
}

# Borrowed-chord candidates (chromatic offsets from root) used under chaos.
BORROWED_CHORD_OFFSETS = [1, 6, 8]  # bII, bV, bVI — spice degrees


def note_to_pc(name: str) -> int:
    if name not in NOTE_TO_PC:
        raise ValueError(f"Unknown note name: {name!r}")
    return NOTE_TO_PC[name]


def scale_pitches(key: str, scale: str) -> list[int]:
    """Pitch classes (0-11) of the scale in the given key."""
    root = note_to_pc(key)
    if scale not in SCALES:
        raise ValueError(f"Unknown scale: {scale!r}")
    return [(root + iv) % 12 for iv in SCALES[scale]]


def scale_degree_pitch(key: str, scale: str, degree: int, octave: int = 4) -> int:
    """
    Absolute MIDI pitch for a scale degree. Degree may exceed the scale length;
    it wraps with octave displacement. octave=4 puts the root near middle C
    (MIDI 60 region: C4 = 60).
    """
    intervals = SCALES[scale]
    n = len(intervals)
    root = note_to_pc(key)
    oct_shift, idx = divmod(degree, n)
    semitone = intervals[idx]
    return (octave + 1) * 12 + root + semitone + oct_shift * 12


def triad(key: str, scale: str, degree: int, octave: int = 4) -> list[int]:
    """Diatonic triad (root, third, fifth) stacked from a scale degree."""
    return [
        scale_degree_pitch(key, scale, degree, octave),
        scale_degree_pitch(key, scale, degree + 2, octave),
        scale_degree_pitch(key, scale, degree + 4, octave),
    ]


def seventh(key: str, scale: str, degree: int, octave: int = 4) -> list[int]:
    """Diatonic seventh chord."""
    return triad(key, scale, degree, octave) + [
        scale_degree_pitch(key, scale, degree + 6, octave)
    ]


def chord_root_pitch(key: str, scale: str, degree: int, octave: int = 2) -> int:
    """Root note in bass register (for BASS_808)."""
    return scale_degree_pitch(key, scale, degree, octave)


def nearest_in_register(pitch: int, lo: int, hi: int) -> int:
    """Octave-shift a pitch until it falls within [lo, hi]."""
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    # clamp as a final safety
    return max(lo, min(hi, pitch))


def is_in_scale(pitch: int, key: str, scale: str) -> bool:
    return (pitch % 12) in scale_pitches(key, scale)
