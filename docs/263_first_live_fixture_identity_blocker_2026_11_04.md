# 2.6.3 — First live fixture identity blocker fixed (4 Nov 2026)

## Observed actual blocker
The workflow `.github/workflows/263-quad-forward-on-request.yml` called `analyze_named_match_gate.run`, which defaulted to `data/match_registry.json`. That file **did not exist on the repository experiment branch**, so the Registry constructor silently loaded an EMPTY registry, making official fixture lookups fail for EVERY match.

## Narrow fix
Use the already-committed `experiments/263/evidence/identity_index_263.json` as the live named-match gate's default. Reuse the existing SHA/UUID validator and 2026/27 league-season membership gate in `mackolik_identity_gate_263.py`. No new teams / fixture IDs are fabricated. Explicit registry paths remain supported for old test callers. Absent explicit file now fails closed.

## First real fixture check
At the time of writing TFF's [4 November official weekly programme](https://www.tff.org/default.aspx?ftxtID=2966&pageID=600) lists `GAZİANTEP FK – KASIMPAŞA A.Ş.` on **6 November 2026 20:00 Turkey** (17:00 UTC). This is a FIXTURE VERIFICATION, not a match prediction.

A new single isolated GitHub workflow tests both the existing synthetic overrides and the canonical read-only index, then invokes the *actual network-fetched* official TFF named-match parser once. It stores a blocked or ready gate report. This is not a simulated fixture pretending to be a real lookup.

## Still not claimed
- The updated `4,509` data file is machine-stage, **not** human source accepted. `data/quad_accepted_263` remains absent.
- The scheduled **6–8 November** 96-candidate cohort, B/C2/C3/M4 formulas, M4 lock, and odds rules unchanged. No first pilot prediction or betting recommendation is created by this check.
- If official live parser cannot extract the match, report the reason and fix the parser from its real diagnostic; do not fake the returned kickoff.

**Single next dependency** after fixture gate passes: approved current-year snapshot in the already-existing 4-model forward workflow, which must be created by authentic source reviewer (or a separately declared unverified research shadow with no claim of human approval).
