"""
Seeded RNG. Every cook is fully reproducible from its seed; recklessness
(chaos) is safe because the same seed always yields the same beat.

We derive independent named streams from the master seed so that, e.g.,
regenerating the LEAD doesn't perturb the drums.
"""
from __future__ import annotations

import hashlib
import random


def _derive(seed: int, stream: str) -> int:
    h = hashlib.sha256(f"{seed}:{stream}".encode()).hexdigest()
    return int(h[:16], 16)


class CookRandom:
    """A bundle of named, independently-seeded random streams."""

    def __init__(self, seed: int):
        self.seed = seed
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        if name not in self._streams:
            self._streams[name] = random.Random(_derive(self.seed, name))
        return self._streams[name]
