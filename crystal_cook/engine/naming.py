"""
Cook folder naming: cooks/YYYY-MM-DD-<adjective>-<noun>/

Names are seeded so a given seed always produces the same name, but two cooks
on the same day with different seeds get distinct folders.
"""
from __future__ import annotations

from datetime import date

# Vocabulary leans into the Crystal Chop aesthetic: beauty vs. grime.
ADJECTIVES = [
    "velvet", "rusted", "midnight", "molten", "glass", "smoked", "fractured",
    "amber", "obsidian", "drowsy", "gilded", "ashen", "neon", "muddy",
    "crystalline", "bruised", "silken", "tarnished", "violet", "hollow",
    "feral", "lucid", "dusty", "frozen", "burning", "sullen", "opaline",
]

NOUNS = [
    "cathedral", "switchblade", "monsoon", "alleyway", "comet", "furnace",
    "lullaby", "static", "pendulum", "marrow", "halo", "undertow", "cinder",
    "lantern", "riptide", "seance", "vellum", "thorn", "echo", "specter",
    "lotus", "anvil", "mirage", "quartz", "raincheck", "vesper", "tidewater",
]


def cook_name(seed: int, on: date | None = None) -> str:
    on = on or date.today()
    adj = ADJECTIVES[seed % len(ADJECTIVES)]
    noun = NOUNS[(seed // len(ADJECTIVES)) % len(NOUNS)]
    return f"{on.isoformat()}-{adj}-{noun}"
