"""
Render a Song to a multi-track MIDI file with embedded CC gestures.

Each role becomes its own MIDI track on its own channel, named by role, so the
arrangement imports cleanly. Gesture curves are sampled into discrete CC
messages. (In the .flp path — Stage 3 — these become native automation clips
instead; see SPEC.)
"""
from __future__ import annotations

import math
from pathlib import Path

import mido

from .macros import NAME as MACRO_NAME
from .model import GestureShape, Role, Song, Stem

PPQ = 480
CC_STEP_BEATS = 0.125  # resolution for sampling ramp/swell/drift curves

# Stable channel assignment per role (0-15).
ROLE_CHANNEL = {r.value: i for i, r in enumerate(Role)}


def _beat_to_tick(beat: float) -> int:
    return max(0, int(round(beat * PPQ)))


def _sample_gesture(g) -> list[tuple[float, int]]:
    """Return [(beat, value), ...] for a gesture curve."""
    shape = g.shape
    if shape == GestureShape.CUT.value or g.end_beat <= g.start_beat:
        return [(g.start_beat, g.value_end)]

    span = g.end_beat - g.start_beat
    n = max(1, int(math.ceil(span / CC_STEP_BEATS)))
    pts: list[tuple[float, int]] = []
    for i in range(n + 1):
        t = i / n
        beat = g.start_beat + t * span
        if shape == GestureShape.RAMP.value:
            val = g.value_start + (g.value_end - g.value_start) * t
        elif shape == GestureShape.SWELL.value:
            # Ease-in swell: slow start, accelerating rise.
            val = g.value_start + (g.value_end - g.value_start) * (t ** 1.6)
        elif shape == GestureShape.DRIFT.value:
            # Gentle sinusoidal wander between start and end.
            mid = (g.value_start + g.value_end) / 2
            amp = (g.value_end - g.value_start) / 2
            val = mid + amp * math.sin(2 * math.pi * t)
        else:
            val = g.value_end
        pts.append((beat, max(0, min(127, int(round(val))))))
    return pts


def _stem_events(stem: Stem, channel: int) -> list[tuple[int, mido.Message]]:
    """Build (abs_tick, message) pairs for one stem's notes and gestures."""
    events: list[tuple[int, mido.Message]] = []

    for n in stem.notes:
        on_tick = _beat_to_tick(n.start_beat)
        off_tick = _beat_to_tick(n.start_beat + n.duration_beats)
        if off_tick <= on_tick:
            off_tick = on_tick + 1
        events.append((on_tick, mido.Message(
            "note_on", note=n.pitch, velocity=n.velocity, channel=channel)))
        events.append((off_tick, mido.Message(
            "note_off", note=n.pitch, velocity=0, channel=channel)))

    for g in stem.gestures:
        for beat, val in _sample_gesture(g):
            events.append((_beat_to_tick(beat), mido.Message(
                "control_change", control=g.target_cc, value=val, channel=channel)))

    return events


def render(song: Song, out_path: Path) -> Path:
    mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)

    # Track 0: tempo + time signature.
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name="CRYSTAL COOK", time=0))
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(song.bpm), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    mid.tracks.append(meta)

    for stem in song.stems:
        track = mido.MidiTrack()
        track.append(mido.MetaMessage("track_name", name=stem.role, time=0))
        channel = ROLE_CHANNEL.get(stem.role, 0)

        events = _stem_events(stem, channel)
        # Stable sort: note_off before note_on at the same tick; CC first.
        order = {"control_change": 0, "note_off": 1, "note_on": 2}
        events.sort(key=lambda e: (e[0], order.get(e[1].type, 3)))

        prev = 0
        for abs_tick, msg in events:
            delta = abs_tick - prev
            prev = abs_tick
            track.append(msg.copy(time=delta))
        mid.tracks.append(track)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(out_path)
    return out_path
