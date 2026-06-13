"""
Standardized macro CC map — identical across all presets, so the generator
never needs to know which preset is loaded.

Confirmed by the user (2026-06-13).
"""

SPACE = 1     # CC1  — reverb send/size
CUTOFF = 74   # CC74 — filter brightness (degrades gracefully on 3rd-party synths)
WIDTH = 9     # CC9  — stereo width
DRIVE = 12    # CC12 — saturation (primarily the 808)

ALL = (SPACE, CUTOFF, WIDTH, DRIVE)

NAME = {SPACE: "SPACE", CUTOFF: "CUTOFF", WIDTH: "WIDTH", DRIVE: "DRIVE"}
