# CRYSTAL COOK — System Specification

> Personal beat generation system for Crystal Chop (trap/hip-hop, chopped samples, beauty vs. grime).
> One command (`cook`) → dated folder → complete FL Studio project skeleton.

---

## Mission

One command produces a dated folder containing a complete, musically coherent beat skeleton: a full song arrangement (not just a loop), with role-tagged stems, embedded automation gestures, and — in later stages — a ready-to-open `.flp` with actual plugins loaded and presets cast per role.

---

## Build Stages

Each stage is independently usable. Do not skip ahead.

### Stage 1 — PyFLP Spike (de-risk first)

Verify PyFLP can round-trip a project from the target FL Studio version.

- Open a hand-built template `.flp`
- Programmatically add one pattern with notes
- Save as a copy
- Confirm it opens cleanly in FL

If PyFLP fails against the target FL version: document it and fall back to multi-track MIDI output + template project for all later stages.

**Blockers:** FL Studio version + OS, template `.flp` (may need to be created first — see Open Questions).

### Stage 2 — Generation Engine

Pure Python library, no FL dependency. Outputs one multi-track `.mid` per cook (CC gestures embedded) into `cooks/YYYY-MM-DD-<adjective>-<noun>/`.

All musical logic lives here. Co-producer readiness requirements (manifest schema, versioning, edit primitives) are baked in here — not retrofitted.

### Stage 3 — FLP Writer

Inject the generated arrangement into a copy of the template `.flp`:

- Patterns placed in the playlist in song order
- Tracks named by role
- Native FL automation clips (preferred over embedded CC when writing `.flp`)

### Stage 4 — Preset Casting

- Read the FL plugin database to know what's installed
- Index saved `.fst` presets (tagged by role + vibe)
- Each cook "casts" the beat: picks a preset per role and loads it on the right channel in the project copy

### Stage 5 — Sample Matcher

Given the cook's key and BPM, search the sample library for candidate chops/loops (filename tags first; audio analysis later if needed) and copy 3–5 candidates into the cook folder.

### Stage 6 — Custom Drum/808 Plugin (JUCE)

Do not start until Stages 1–4 work end to end.

Synthesized voices:
- **808**: sine + pitch-envelope attack, saturation, glide on overlapping notes
- **Kick**: shorter/punchier variant of the same recipe, tuned for boom-bap layering
- **Hats**: filtered square stack
- **Snare**: tuned sines + noise burst

Build standalone-first for fast listen-loop iteration. Every tuning constant is a parameter.

### Stage 7 — Co-producer Agent Layer

Tier 1 (free): Claude Code acts as co-producer by reading/editing manifests and re-running the CLI.

Tier 2 (later): MCP server exposing tools:
- `generate_beat`
- `edit_section`
- `mutate_stem`
- `recast_preset`
- `revert_to_version`

### Stage 8 — Sample Chopper Module (`chop` command)

Ingest an audio file (a record to flip) and produce a chop folder that can optionally seed a cook.

**Pipeline:**

1. **Separation** — Demucs (local) splits into vocals / drums / bass / other, so the musical bed can be chopped without the original drummer fighting the new one.
2. **Analysis** — key + scale estimate, tempo, downbeat grid, novelty curve, chroma self-similarity, rough chord skeleton per bar. Written to `analysis.json`. Key/chord estimates are GUESSES — surfaced for correction; never treated as ground truth.
3. **Chop candidates** — onset/downbeat-aligned slice candidates scored for choppability (clean attack, harmonic coherence, spectral interest, quantizes to a musical division). Export top ~12 as numbered WAVs with start/end metadata. Machine measures; ears decide.

**Style modes** (parameter presets on the chop arranger):
- `dilla` — drunk microtiming; slices deliberately off-grid; swing pushed past comfortable
- `madlib` — longer loop slices, abrupt cuts, keep the dirt and vinyl noise, sudden texture switches at section boundaries
- `ninth` — short soul chops pitched up 2–4 semitones, 2–4 chop patterns in call-and-response

**Handoff to cook engine:**
`cook --sample <chopfolder>` treats chops as a `CHOPS` role stem and generates complementary stems around the sample:
- 808/bass follows the sample's chord skeleton
- COUNTER fills the sample's rests
- Drums inherit the sample's swing
- Gestures apply as normal

**Inspire mode:**
`cook --inspire <audiofile>` analyzes a reference track and derives a REFERENCE PROFILE — same schema as a genre profile, but extracted from audio: BPM, key/mode, swing from onset microtiming, per-band density character, brightness baseline for cutoff gestures, section structure and energy arc from novelty/self-similarity analysis. No audio from the reference enters the output — measurements only. Reference profiles compose like any profile: blendable with genre profiles by weight, chaos-compatible, freezable into a named profile.

---

## Core Data Model

### Song
```
key: str                  # e.g. "F#"
scale: str                # e.g. "minor"
bpm: float
sections: List[Section]
global_swing: float       # 0.0–1.0
seed: int                 # every cook is reproducible from its seed
```

### Section
```
type: Literal["INTRO","VERSE","HOOK","BRIDGE","BREAKDOWN","OUTRO"]
length_bars: int          # 4 or 8
energy: float             # 0.0–1.0
active_roles: List[Role]
variation_source: None | SectionRef  # fresh, or derived-from-section-X
variation_ops: List[str]             # e.g. ["rhythmic_displacement"]
```

### Stem
Role-tagged note sequence + gesture list.

**Roles:** `CHORDS`, `LEAD`, `COUNTER`, `BASS_808`, `KICK`, `SNARE`, `HATS`, `PERC` (optional), `CHOPS` (Stage 8)

Role activation comes from the genre profile's activation map. A role the profile deactivates emits no MIDI.

### Gesture
Parametric automation curve:
```
target_cc: int            # see macro CC map
start_bar: int
end_bar: int
shape: Literal["ramp","swell","cut","drift"]
value_start: int          # 0–127
value_end: int            # 0–127
```

### Energy Curve
Per-section scalar (0.0–1.0) driving:
- Discrete decisions: stem activation, note density, octave/register, hat roll frequency
- Continuous gestures: amplitudes of the macro CCs

---

## Standardized Macro CC Map

Identical across all presets — the generator never needs to know which preset is loaded.

| CC  | Macro   | Description                                    |
|-----|---------|------------------------------------------------|
| 1   | SPACE   | Reverb send/size                               |
| 74  | CUTOFF  | Filter brightness (degrades gracefully on 3rd-party synths) |
| 9   | WIDTH   | Stereo width                                   |
| 12  | DRIVE   | Saturation (primary use: 808)                  |

Smoothing/slewing of incoming CC is the synth's job (Stage 6), not the generator's.

---

## Arrangement Rules (defaults; all overridable)

**Default song form:**
```
INTRO(8) → VERSE(8) → HOOK(8) → VERSE(8) → HOOK(8) → BREAKDOWN(4–8) → HOOK(8) → OUTRO(4)
```

**Variation rules:**
- Verse 2 derives from Verse 1 via melodic fragment reuse + rhythmic displacement — never verbatim copy

**Transition logic:**
- Bar before hook: mute
- Hat rolls into downbeats
- Fill density rises with target-section energy

---

## Gesture Rules (the signature moves)

- **SPACE** swells through the bar before each hook, then cuts dry on the downbeat
- **CUTOFF** starts closed in intros/breakdowns, opens across the transition
- **WIDTH** narrow verses → wide hooks → mono breakdown (so hook lands huge)
- **DRIVE** on BASS_808 scales with section energy
- **Drums** NEVER receive SPACE swells (always near-dry)
- **COUNTER** gets one slow drift per section so static passages breathe
- **Ending**: either all sends killed for a dry final hit, OR one note rings into max SPACE as outro tail — coin-flip per cook

---

## Musical Engine Rules

### Genre is data, not code

A genre is a YAML profile file (`profiles/trap.yaml`, `profiles/boombap.yaml` ship first) declaring:
- BPM range
- Role activation map
- Swing amount + which roles it applies to
- Rhythm character per drum role
- Progression family weights
- Gesture tendencies
- Density curves

The engine reads profiles. It contains no genre-specific branches. New genres are new YAML files.

**`trap.yaml` defaults:**
- BPM 130–160, halftime feel
- 808 carries the low end with glides
- Sparse or absent KICK
- Hat rolls / syncopation
- Swing on hats only

**`boombap.yaml` defaults:**
- BPM 80–96
- KICK + SNARE backbone (kicks syncopated against 2/4 snare backbeat, ghost-note variation)
- Swing on the whole kit
- Bass as root-note support
- CHOPS typically the lead voice
- Stage 8 style modes (dilla/madlib/ninth) imply boom-bap

### Hybrids

Weighted blends, not new code: `--genre trap:0.6+boombap:0.4`

Interpolates continuous parameters, probabilistically samples discrete ones (role activation, progression family). Any working blend can be frozen into a named profile:
```
cook --freeze-profile <manifest> <name>
```

### Chaos knob

`--chaos 0.0–1.0` — a knob, not a genre; composable with any profile or blend.

- **Low**: looser quantize and voicing rules
- **Mid**: borrowed chords beyond diatonic set, odd section lengths (3/5/7 bars), form-grammar mutations
- **High**: polymetric stems (e.g. hats in 3 over drums in 4), non-resolving progressions, role rule-breaking (808 in melody register)

Chaos level recorded in manifest; seeded reproducibility makes recklessness safe.

### Default aesthetic

- Minor keys weighted heavily
- Dark/moody progressions favored (i–VI–III–VII family and variants)
- Occasional borrowed-chord spice at low probability
- LEAD on top of the chord bed
- COUNTER is call-and-response against LEAD (fills LEAD's rests)
- BASS_808 follows chord roots; overlapping notes = glide intended
- BPM defaults from genre profile

---

## Engineering Conventions

- **Python 3.11+**
- **Dependencies:** `mido` (MIDI), `pyflp` (FLP), `librosa`/`madmom` + Demucs (Stage 8 audio analysis), `pytest` (tests)
- Generation logic importable and UI-agnostic (potential JUCE wrapper)

### CLI

Single entry point `cook` with flags:

| Flag | Description |
|------|-------------|
| `--key` | Root key |
| `--bpm` | Tempo |
| `--genre <profile \| name:wt+name:wt>` | Genre profile or weighted blend |
| `--chaos 0..1` | Experimental looseness knob |
| `--seed` | Reproducibility seed |
| `--form` | Override song form string |
| `--bars` | Override section bar counts |
| `--sample <chopfolder>` | Seed cook from a chop folder |
| `--inspire <audiofile>` | Derive reference profile from audio |
| `--from <manifest>` | Re-render from a manifest |
| `--diff <v> <v>` | Human-readable diff between two manifest versions |
| `--stats <manifest>` | Per-section density/register/brightness/energy summary |
| `--freeze-profile <manifest> <name>` | Write resolved parameters as a named profile |

Sibling command: `chop <audiofile>`

### Output structure

```
cooks/
  YYYY-MM-DD-<adjective>-<noun>/
    cook.json          # canonical manifest (see below)
    cook_v2.json       # edit versions, each with parent + changelog
    output.mid         # multi-track MIDI with CC gestures
    output.flp         # (Stage 3+) FL Studio project copy
    samples/           # (Stage 5+) matched sample candidates
```

---

## Co-producer Readiness (baked into Stage 2)

### The manifest IS the beat

`cook.json` fully determines the output: seed, key, BPM, form, per-section parameters, per-stem note data or derivation rules, gestures, cast presets, matched samples. Re-rendering from a manifest must be deterministic.

### Versioning, never destruction

Edits write `v2.json`, `v3.json`, … in the same cook folder. Each version has:
- `parent`: reference to the version it was derived from
- `changelog`: one human-readable sentence describing what changed and why

"Go back to v3 but keep the v5 hats" must be expressible.

### First-class edit operations

These are library functions, not logic buried in generation:

| Operation | Signature |
|-----------|-----------|
| `set_section_energy` | `(section, energy: float)` |
| `regenerate_stem` | `(role, section, keep_rhythm=False, keep_pitches=False)` |
| `transpose` | `(role, sections, interval: int)` |
| `extend_section` | `(section, bars: int)` |
| `swap_progression` | `(section, progression_key: str)` |
| `recast_preset` | `(role, vibe: str)` |
| `thin_density` | `(role, section, factor: float)` |

The `keep_rhythm` / `keep_pitches` decomposition in `regenerate_stem` is the most important primitive — implement early and well.

### Vibe vocabulary table

A YAML file (`vibe_vocab.yaml`) mapping words to parameter moves:
- `"darker"` → mode/register/cutoff-baseline shifts
- `"more bounce"` → swing + syncopation density
- `"too clean"` → drive up + humanization jitter + dustier sample cast

This file grows over time; the agent consults and proposes additions.

### Legible edits

Any agent-driven change is explainable in one sentence referencing concrete before/after values, sourced from the manifest diff.

### `--stats` command (deaf-agent guardrails)

Emits per-section density/register/brightness/energy summaries so the agent can sanity-check structure without ears ("is the hook actually bigger than the verse?").

---

## Open Questions (pending answers before Stage 1)

1. **FL Studio version + OS**, and paths to:
   - FL user data folder
   - Plugin database
   - Saved `.fst` presets
   - Sample library
2. **Confirm or adjust the macro CC assignments** (CC1=SPACE, CC74=CUTOFF, CC9=WIDTH, CC12=DRIVE)
3. **Preferred keys, BPM range, and swing amount** for personal defaults
4. **Template `.flp`**: does one exist? If not, walkthrough needed: role tracks, mixer routing, sends, macro-mapped presets.
