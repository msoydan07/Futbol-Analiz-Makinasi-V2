# REAL SOURCE BRIDGE AND RESEARCH INFERENCE STATUS — 2026-11-09

## Executed, verified
1. Inspected existing 2.6.3 official on-demand gate: `analyze_named_match_gate.run`.
   If official-source lookup is not `VERIFIED`, new adapter refuses
   to produce a future fixture manifest. Canonical IDs from the gate
   are preserved exactly; no name-based fixture identity guessing.
2. Independently audited ten Football-Data 2026/27 score feeds against
   the original 20-league OpenFootball snapshot. Source retrieval worked
   after allowing equivalent official host redirects, **but 0 of 10
   leagues passed exact historical club-name crosswalk acceptance**.
   Therefore this new feed cannot be safely appended to the 18,255-game
   20-league archive. See audit run 42567999656.
3. Found an alternative research-accepted 2.6.3 history source in
   `data/quad_accepted_263/extended_history.csv`. SHA256
   `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`
   **equals the owner's research acceptance SHA**. The data contains
   **4,518** scored matches across all 10 approved leagues, latest
   match 2026-11-03. The owner acceptance says NOT all scores are
   independently verified. The adapter is research-only.
4. `trusted_263_snapshot_bridge.py` exports those 4,518 rows into
   the existing XGBoost input schema, using actual immutable 2.6.3
   club IDs as feature identities. It now fails closed if the accepted
   bytes SHA does not match.
5. `official_263_fixture_bridge.py` consumes only the existing
   actual officially VERIFIED on-demand gate, carries its IDs and
   source timestamp into the XGBoost manifest. Synthetic unit tests
   confirm rejection of NOT_VERIFIED, stale and mismatching identities.
6. **Full integration success**: pinned XGBoost code trains on all
   4,518 owner-accepted historical rows, predicts an explicitly
   **fictional future fixture** using unchanged canonical team IDs,
   and the research SHA seal writes once / refuses a duplicate.
   No fictional fixture is represented as a genuine match.
   Workflow: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42568461375
7. Read-only snapshot and official fixture source QA:
   https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42568362588
   Fresh 20-league crosswalk blocked audit:
   https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42567999656

## IMPORTANT technical distinction
Previous favorable XGBoost log loss was from a **different
20-league 18,255-game training context**, with 2026/27 historical
evaluations. This bridge trains the same algorithm/hyperparameters on
the owner-accepted **ten-league 4,518-game data context**. Its accuracy
and calibration have **NOT yet been independently measured**. Do not
transfer the earlier 20-league performance numbers to this version.
Do not replace the original 2.6.3 M4 or claim financial advantage.

## Remaining work before actual future matchup
- An actual upcoming fixture must be checked through the unmodified
  official on-demand gate; no match was requested/selected in this task.
- Source snapshot should be updated for Nov 4 onward before a later
  fixture and checked independently as far as possible; expired history
  fails the date check.
- The ten-league adapted XGBoost needs its own leakage-safe
  historical chronological performance audit on equal fixtures vs M4.
- A prospective research seal must be committed to an append-only
  GitHub record or equivalent trusted time-stamped store; a local file
  is not independently durable across workflow runs.
- Only after technical and predictive acceptance should any main
  version bump or 2.6.3 architecture change be discussed.

## Status
HISTORICAL_SCORE_CANONICAL_BRIDGE: PASS (4,518 rows, owner-accepted)
OFFICIAL_GATE_ADAPTER_UNIT_TESTS: PASS
SYNTHETIC_END_TO_END_ML_INFERENCE_AND_LOCAL_SHA_SEAL: PASS
LIVE_FUTURE_FIXTURE_FORECAST_SEALED: NO
FULL_20_LEAGUE_CURRENT_FEED_CROSSWALK: BLOCKED (0/10)
PRODUCTION_2_6_3_CHANGED: NO
