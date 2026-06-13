# CRYSTAL COOK — Backlog & Design Notes

Running log of feedback and design decisions across sessions. Newest first.

---

## Validation status

- **Stage 1 (PyFLP spike):** PASS — confirmed opening in FL Studio 25.2.5.
- **Stage 2 (generation engine):** Working; user confirms cooks "sound pretty
  solid for no FX or instruments." Timing bug at verse-2 / pre-hook fills fixed
  (commit 111606c).

---

## Open feedback (from listening sessions)

1. **Drums feel slightly off.** User suspects plugin/sample selection rather
   than note timing. Revisit AFTER template exists with real drum sounds; if
   still off, look at swing application + humanization jitter on the kit.
   (Low priority until confirmed it's not sound selection.)
2. **"More structural issues" — pending.** User is holding a list; collect next
   session.
3. **Flat single-pattern-per-instrument output is unnatural.** See Stage 3
   design below. This is the big one.

---

## Stage 3 design decision: pattern breakout & auto-arrangement

**Problem (user, 2026-06-13):** "Project files written in a single pattern for
every instrument is a rare event. Typically patterns are broken out for
variation, organization, and layering."

**Why it's deferred to Stage 3, not fixed in MIDI:** a standard `.mid` file has
no concept of FL "patterns" — only continuous tracks. Pattern breakout is
inherently an FL-project (FLP-writer) feature. The flat MIDI is a Stage 2
validation artifact.

**The data model already supports this for free:**
- every `Note` carries `section_index`
- every `Section` has a `type` and `length_bars`
- derived sections carry `variation_source` (which section they came from)

**Plan for the FLP writer:**
1. Author one FL **Pattern** per (role × section) — e.g. `HATS_HOOK`,
   `LEAD_VERSE1`, `LEAD_VERSE2`, `808_BREAKDOWN`. Group/color by section.
2. Place those patterns in the **playlist** at their real bar offsets so the
   arrangement is laid out, not buried in one clip.
3. **Identical sections share one pattern.** The form has HOOK ×3; if their
   note content is identical, write ONE `HOOK` pattern and reference it 3× in
   the playlist (how a producer actually works; edit-once propagates).
4. **Derived sections get their own pattern.** VERSE 2 is non-verbatim
   (bar-shifted), so it becomes `LEAD_VERSE2` rather than reusing VERSE1.

**Open question for next session (needs user call):**
- Should repeated HOOKs **share** one pattern (edit-once updates all three —
  matches manual workflow) or be **independent clones** (edit each separately)?
  Leaning shared-by-default with a `--clone-sections` escape hatch.

**Bonus this unlocks:** finer-grained co-producer edits. "Regenerate the hook
hats" becomes "regenerate the `HATS_HOOK` pattern." Makes the FL project
navigable and the manifest edits map 1:1 onto FL patterns.

**Layering note:** user also mentioned "layering" (e.g. KICK under 808, stacked
hat layers). Partly a generation/profile concern, partly FL channel routing —
revisit once the template's channel/mixer structure is known.

---

## Blocking dependency

Stage 3 cannot start until the user provides the **template `.flp`** (role
channels + mixer routing + sends + macro targets). Macro-mapping checklist owed
to the user when they begin building it.
