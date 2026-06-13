"""
Stage 2 musical-invariant tests (from SPEC):
- notes in key (melodic roles at chaos=0)
- no role writes outside its register
- gesture curves bounded 0-127
- verse-2 != verse-1 verbatim
- determinism: same seed -> same beat
- manifest round-trips and re-renders deterministically
"""
import pytest

from crystal_cook.engine import theory
from crystal_cook.engine.cook import CookParams, build_song
from crystal_cook.engine.manifest import Manifest
from crystal_cook.engine.model import (
    MELODIC_ROLES, REGISTER, Role, SectionType,
)

GENRES = ["trap", "boombap", "trap:0.5+boombap:0.5"]
SEEDS = [1, 42, 7, 100, 2024]


def _song(genre="trap", seed=42, chaos=0.0, **kw):
    s, _ = build_song(CookParams(genre=genre, seed=seed, chaos=chaos, **kw))
    return s


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("genre", GENRES)
def test_melodic_notes_in_key_at_chaos_zero(genre, seed):
    song = _song(genre=genre, seed=seed, chaos=0.0)
    melodic = {r.value for r in MELODIC_ROLES}
    for stem in song.stems:
        if stem.role not in melodic:
            continue
        for n in stem.notes:
            assert theory.is_in_scale(n.pitch, song.key, song.scale), (
                f"{stem.role} note {n.pitch} out of key {song.key} {song.scale}"
            )


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("genre", GENRES)
def test_no_role_writes_outside_register(genre, seed):
    song = _song(genre=genre, seed=seed, chaos=0.6)
    for stem in song.stems:
        lo, hi = REGISTER[Role(stem.role)]
        for n in stem.notes:
            assert lo <= n.pitch <= hi, (
                f"{stem.role} note {n.pitch} outside register [{lo},{hi}]"
            )


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("genre", GENRES)
def test_gesture_curves_bounded(genre, seed):
    song = _song(genre=genre, seed=seed, chaos=0.5)
    for stem in song.stems:
        for g in stem.gestures:
            assert 0 <= g.value_start <= 127, f"{g} value_start out of range"
            assert 0 <= g.value_end <= 127, f"{g} value_end out of range"
            assert g.end_beat >= g.start_beat


@pytest.mark.parametrize("seed", SEEDS)
def test_verse2_not_verbatim_verse1(seed):
    song = _song(genre="boombap", seed=seed, chaos=0.0)
    verses = [i for i, s in enumerate(song.sections) if s.type == SectionType.VERSE.value]
    if len(verses) < 2:
        pytest.skip("form has fewer than two verses")
    v1, v2 = verses[0], verses[1]
    # The second verse must be marked as derived.
    assert song.sections[v2].variation_source == v1
    lead = song.stem(Role.LEAD.value)
    if lead is None:
        pytest.skip("LEAD inactive this cook")
    n1 = [(n.start_beat, n.pitch) for n in lead.notes if n.section_index == v1]
    n2 = [(n.start_beat, n.pitch) for n in lead.notes if n.section_index == v2]
    # Normalize verse 2 onsets back to verse-1's time frame for comparison.
    off = song.section_beat_range(v2)[0] - song.section_beat_range(v1)[0]
    n2n = sorted((round(b - off, 4), p) for b, p in n2)
    assert sorted(n1) != n2n, "verse 2 is a verbatim copy of verse 1"


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("genre", GENRES)
def test_determinism(genre, seed):
    a = Manifest(name="a", song=_song(genre=genre, seed=seed)).to_dict()["song"]
    b = Manifest(name="b", song=_song(genre=genre, seed=seed)).to_dict()["song"]
    assert a == b


def test_manifest_roundtrip():
    song = _song(genre="trap", seed=42, chaos=0.3)
    m = Manifest(name="rt", song=song)
    d = m.to_dict()
    m2 = Manifest.from_dict(d)
    assert m2.to_dict() == d


def test_swing_only_on_profile_roles_trap():
    """Trap swings hats only; the kick grid should not carry swing offsets."""
    from crystal_cook.engine.profile import resolve
    p = resolve("trap")
    assert p.swing_roles() == ["HATS"]
    assert p.swing_amount() > 0


def test_blend_interpolates_bpm():
    from crystal_cook.engine.profile import resolve
    p = resolve("trap:0.5+boombap:0.5")
    lo, hi = p.bpm_range()
    # trap 130-160, boombap 80-96 -> midpoint ranges
    assert 100 <= lo <= 115
    assert 120 <= hi <= 135
