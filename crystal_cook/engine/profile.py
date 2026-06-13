"""
Genre profile loading and blending.

Genre is data: each profile is a YAML file. Hybrids are weighted blends, not
new code. `trap:0.6+boombap:0.4` interpolates continuous parameters and merges
discrete weights; discrete decisions (role activation, progression family) are
sampled later, at cook time, from the blended weights using the cook's seed.

Reference profiles (Stage 8 --inspire) share this exact schema, so they
compose with genre profiles identically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROFILES_DIR = Path(__file__).resolve().parents[2] / "profiles"

_BLEND_RE = re.compile(r"^([A-Za-z0-9_]+):([0-9.]+)$")


def _load_raw(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def parse_genre_spec(spec: str) -> list[tuple[str, float]]:
    """
    Parse a --genre string into [(name, weight), ...].

    "trap"                  -> [("trap", 1.0)]
    "trap:0.6+boombap:0.4"  -> [("trap", 0.6), ("boombap", 0.4)]
    """
    spec = spec.strip()
    parts = spec.split("+")
    out: list[tuple[str, float]] = []
    for part in parts:
        part = part.strip()
        m = _BLEND_RE.match(part)
        if m:
            out.append((m.group(1), float(m.group(2))))
        else:
            out.append((part, 1.0))
    total = sum(w for _, w in out)
    if total <= 0:
        raise ValueError(f"Genre weights sum to zero: {spec!r}")
    return [(n, w / total) for n, w in out]  # normalize


def _blend_num(values: list[tuple[float, float]]) -> float:
    """Weighted mean of (value, weight) pairs."""
    return sum(v * w for v, w in values)


@dataclass
class ResolvedProfile:
    """A concrete parameter set, possibly blended from several profiles."""
    spec: str
    data: dict = field(default_factory=dict)

    # ── BPM ──
    def bpm_range(self) -> tuple[float, float]:
        b = self.data["bpm"]
        return float(b["min"]), float(b["max"])

    def bpm_default(self) -> float:
        return float(self.data["bpm"]["default"])

    def feel(self) -> str:
        return self.data["bpm"].get("feel", "straight")

    # ── activation ──
    def activation_weight(self, role: str) -> float:
        return float(self.data.get("activation", {}).get(role, 0.0))

    # ── swing ──
    def swing_amount(self) -> float:
        return float(self.data.get("swing", {}).get("amount", 0.0))

    def swing_roles(self) -> list[str]:
        return list(self.data.get("swing", {}).get("roles", []))

    # ── rhythm ──
    def rhythm(self, role: str) -> dict:
        return dict(self.data.get("rhythm", {}).get(role, {}))

    # ── progressions ──
    def progression_weights(self) -> dict[str, float]:
        return dict(self.data.get("progressions", {}))

    # ── density ──
    def density(self, role: str) -> dict:
        return dict(self.data.get("density", {}).get(role, {"low": 0.5, "high": 1.0}))

    # ── gestures ──
    def gesture(self, key: str) -> float:
        return float(self.data.get("gestures", {}).get(key, 1.0))

    # ── aesthetic ──
    def scale_weights(self) -> dict[str, float]:
        return dict(self.data.get("aesthetic", {}).get("scale_weights", {"minor": 1.0}))

    def borrowed_chord_prob(self) -> float:
        return float(self.data.get("aesthetic", {}).get("borrowed_chord_prob", 0.0))


def _merge(raws: list[tuple[dict, float]]) -> dict:
    """Blend raw profile dicts by weight."""
    out: dict = {}

    # BPM: interpolate min/max/default
    out["bpm"] = {
        "min": _blend_num([(r["bpm"]["min"], w) for r, w in raws]),
        "max": _blend_num([(r["bpm"]["max"], w) for r, w in raws]),
        "default": _blend_num([(r["bpm"]["default"], w) for r, w in raws]),
        # feel: take the highest-weight profile's feel
        "feel": max(raws, key=lambda rw: rw[1])[0]["bpm"].get("feel", "straight"),
    }

    # activation: weighted mean of each role's weight
    roles = set()
    for r, _ in raws:
        roles.update(r.get("activation", {}).keys())
    out["activation"] = {
        role: _blend_num([(r.get("activation", {}).get(role, 0.0), w) for r, w in raws])
        for role in roles
    }

    # swing: interpolate amount; union of roles weighted by majority
    out["swing"] = {
        "amount": _blend_num([(r.get("swing", {}).get("amount", 0.0), w) for r, w in raws]),
    }
    swing_role_score: dict[str, float] = {}
    for r, w in raws:
        for role in r.get("swing", {}).get("roles", []):
            swing_role_score[role] = swing_role_score.get(role, 0.0) + w
    out["swing"]["roles"] = [role for role, s in swing_role_score.items() if s >= 0.5]

    # rhythm: interpolate numeric fields; categorical -> highest-weight profile
    rhythm_roles = set()
    for r, _ in raws:
        rhythm_roles.update(r.get("rhythm", {}).keys())
    out["rhythm"] = {}
    for role in rhythm_roles:
        merged: dict = {}
        keys = set()
        for r, _ in raws:
            keys.update(r.get("rhythm", {}).get(role, {}).keys())
        for k in keys:
            vals = [(r.get("rhythm", {}).get(role, {}).get(k), w) for r, w in raws]
            numeric = [(v, w) for v, w in vals if isinstance(v, (int, float))]
            if numeric and len(numeric) == len([v for v, _ in vals if v is not None]):
                merged[k] = _blend_num(numeric)
            else:
                # categorical / list — take highest-weight non-null
                best = max(
                    [(v, w) for v, w in vals if v is not None],
                    key=lambda vw: vw[1], default=(None, 0),
                )[0]
                merged[k] = best
        out["rhythm"][role] = merged

    # progressions: weighted sum of family weights
    prog: dict[str, float] = {}
    for r, w in raws:
        for fam, fw in r.get("progressions", {}).items():
            prog[fam] = prog.get(fam, 0.0) + fw * w
    out["progressions"] = prog

    # density: interpolate low/high per role
    dens_roles = set()
    for r, _ in raws:
        dens_roles.update(r.get("density", {}).keys())
    out["density"] = {}
    for role in dens_roles:
        out["density"][role] = {
            "low": _blend_num([(r.get("density", {}).get(role, {}).get("low", 0.5), w) for r, w in raws]),
            "high": _blend_num([(r.get("density", {}).get(role, {}).get("high", 1.0), w) for r, w in raws]),
        }

    # gestures: interpolate
    gkeys = set()
    for r, _ in raws:
        gkeys.update(r.get("gestures", {}).keys())
    out["gestures"] = {
        k: _blend_num([(r.get("gestures", {}).get(k, 1.0), w) for r, w in raws])
        for k in gkeys
    }

    # aesthetic
    scale_w: dict[str, float] = {}
    for r, w in raws:
        for sc, sw in r.get("aesthetic", {}).get("scale_weights", {}).items():
            scale_w[sc] = scale_w.get(sc, 0.0) + sw * w
    out["aesthetic"] = {
        "scale_weights": scale_w,
        "borrowed_chord_prob": _blend_num(
            [(r.get("aesthetic", {}).get("borrowed_chord_prob", 0.0), w) for r, w in raws]
        ),
    }

    return out


def resolve(genre_spec: str, extra_profiles: dict[str, dict] | None = None) -> ResolvedProfile:
    """
    Resolve a --genre spec to a concrete ResolvedProfile.

    extra_profiles: optional in-memory profiles (e.g. a reference profile from
    --inspire) keyed by name, taking precedence over disk profiles.
    """
    extra_profiles = extra_profiles or {}
    weights = parse_genre_spec(genre_spec)
    raws: list[tuple[dict, float]] = []
    for name, w in weights:
        raw = extra_profiles.get(name) or _load_raw(name)
        raws.append((raw, w))
    if len(raws) == 1:
        return ResolvedProfile(spec=genre_spec, data=raws[0][0])
    return ResolvedProfile(spec=genre_spec, data=_merge(raws))


def freeze_resolved(genre_spec: str, name: str, overrides: dict | None = None) -> Path:
    """
    Write the resolved parameters of a (possibly blended) genre spec out as a
    new named profile file: `cook --freeze-profile`. Any blend that works can
    become a first-class profile.
    """
    rp = resolve(genre_spec)
    data = dict(rp.data)
    data["name"] = name
    if overrides:
        # Stamp the cook's concrete bpm / swing so the frozen profile reproduces it.
        if "bpm" in overrides:
            data.setdefault("bpm", {})["default"] = overrides["bpm"]
        if "swing" in overrides:
            data.setdefault("swing", {})["amount"] = overrides["swing"]
    out = PROFILES_DIR / f"{name}.yaml"
    with open(out, "w") as f:
        f.write(f"# Frozen profile from spec: {genre_spec}\n")
        yaml.safe_dump(data, f, sort_keys=False)
    return out
