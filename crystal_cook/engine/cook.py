"""
Cook orchestration: profile -> song -> stems -> gestures -> MIDI + manifest.

This is the top-level Stage 2 entry point. `cook()` produces a dated folder
containing cook.json (the manifest) and output.mid. `recook_from_manifest()`
deterministically re-renders any version (used by `cook --from`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import arrange, gestures, render_midi, theory
from .manifest import Manifest, load_manifest
from .model import Role, Song
from .naming import cook_name
from .profile import ResolvedProfile, resolve
from .rng import CookRandom
from .stems import GenContext, generate_all_stems

COOKS_DIR = Path(__file__).resolve().parents[2] / "cooks"


@dataclass
class CookParams:
    genre: str = "trap"
    key: str | None = None
    bpm: float | None = None
    chaos: float = 0.0
    seed: int | None = None
    form: str | None = None
    swing: float | None = None
    extra_profiles: dict | None = None  # in-memory profiles (Stage 8 --inspire)


def _choose_seed(seed: int | None) -> int:
    if seed is not None:
        return seed
    import secrets
    return secrets.randbelow(2**31)


def _choose_scale(profile: ResolvedProfile, rng: CookRandom) -> str:
    weights = profile.scale_weights()
    scales = list(weights.keys())
    r = rng.stream("scale")
    return r.choices(scales, weights=[weights[s] for s in scales], k=1)[0]


def _choose_key(rng: CookRandom) -> str:
    # Roots common in moody production; minor-ness comes from the scale choice.
    roots = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return rng.stream("key").choice(roots)


def build_song(params: CookParams) -> tuple[Song, str]:
    """Build a fully-realized Song and pick the ending mode. Deterministic per seed."""
    seed = _choose_seed(params.seed)
    rng = CookRandom(seed)
    profile = resolve(params.genre, extra_profiles=params.extra_profiles)

    scale = _choose_scale(profile, rng)
    key = params.key or _choose_key(rng)
    bpm = params.bpm if params.bpm is not None else profile.bpm_default()
    swing = params.swing if params.swing is not None else profile.swing_amount()

    sections = arrange.build_sections(profile, rng, params.chaos, params.form)

    ctx = GenContext(
        key=key, scale=scale, profile=profile, rng=rng,
        chaos=params.chaos, sections=sections,
    )
    stem_list = generate_all_stems(ctx)
    stems_by_role = {s.role: s for s in stem_list}

    ending_mode = "ring" if rng.stream("ending").random() < 0.5 else "dry"
    gestures.generate_gestures(ctx, stems_by_role, ending_mode)

    song = Song(
        key=key, scale=scale, bpm=bpm, seed=seed, chaos=params.chaos,
        genre_spec=params.genre, global_swing=swing,
        sections=sections, stems=stem_list,
    )
    return song, ending_mode


def cook(params: CookParams, cooks_dir: Path | None = None) -> tuple[Path, Manifest]:
    """Run a full cook. Returns (cook_dir, manifest)."""
    cooks_dir = cooks_dir or COOKS_DIR
    song, ending_mode = build_song(params)

    name = cook_name(song.seed)
    cook_dir = cooks_dir / name

    manifest = Manifest(name=name, song=song, ending_mode=ending_mode)
    manifest.save(cook_dir)
    render_midi.render(song, cook_dir / "output.mid")
    return cook_dir, manifest


def recook_from_manifest(manifest_path: Path) -> Path:
    """Re-render MIDI from a manifest (deterministic). Used by `cook --from`."""
    manifest = load_manifest(manifest_path)
    out = manifest_path.parent / "output.mid"
    render_midi.render(manifest.song, out)
    return out
