# Model Challenge — frozen research protocol (2026-11-09)

## Goal and scope
Compare independent match-outcome (1-X-2) forecasters with the existing B/C2/C3/M4 system, without modifying any prior forecast, calibration lock, source acceptance or pilot results. This branch is experimental; no wagering authorization or revenue claim.

## Sources / rights
Initial transparent baseline: [OpenFootball football.json](https://github.com/openfootball/football.json), CC0-1.0 repository license, pinned to commit `e6744429ee395bc86f247348c6184bb08d4eb361`. Public results are **not** xG, player availability, betting odds or timestamped pre-match features. Repository attribution and per-file provider provenance should be retained. Alternative dataset [eatpizzanot/soccer-dataset](https://huggingface.co/datasets/eatpizzanot/soccer-dataset) is **candidate only** until redistribution rights, time-of-knowledge, quality, and data schema are independently verified. Do not scrape football-data.co.uk without checking permission for automated use.

## Data acceptance
A league-season may enter the normalized *research* archive when source is available and pinned, team IDs unique after mapping, scores full-time and nonnegative, dates parsable, duplicate fixture keys absent, and count/missing-rate report saved. Do not silently use listed but unplayed fixtures. Reject self-play, exact duplicates with conflicting scores, post-dated matches, and bad scores. Preserve provenance SHA-256 per input plus generated normalized dataset digest; preserve missing leagues in a coverage report (not fabricated rows). Start with available league/seasons, not a guaranteed 20 complete historical leagues. 2025/26 OpenFootball covers 19 of the originally suggested 20 competitions; National League is missing. Austrian second tier (at.2) can be investigated as a replacement, making *possible* 20 but not guaranteeing four years of coverage.

## Model contest
1. Locked incumbent: original B/C2/C3/M4, same published input cutoff and prediction rules. If exact historical as-of reconstruction is impossible, mark `NOT_COMPARABLE`; do NOT call new retrospective predictions frozen historical incumbent predictions.
2. Rating baseline: causal Elo with home advantage and regularization, evaluated only after matches have entered training history.
3. Statistical baseline: regularized Poisson/Dixon-Coles with time-decay; optimize parameters on training/development only.
4. ML challenger: XGBoost/CatBoost with train-only encoders, *shifted* rolling form, current-season strength and rest; no current match stats, odds, post-match xG or other future inputs.
5. Predeclared combination can be tuned on development only; never pick based on holdout outcomes.

## Split policy / leakage
Calendar-time chronological train, development and untouched holdout, with season-aware walk-forward refits; fixed split dates must be chosen and published before testing based on each league's actual coverage. No random train/test split. Compare identical eligible fixtures for all contenders. Fit imputers, league ratings, calibration, feature encoders and hyperparameters strictly on information preceding the scored fixture. Today's score must never appear in its own input or in opponent strength at kickoff. Retain `as_of` metadata.

## Evaluation and promotion
Primary: multiclass log loss and Brier, each on the *same* fixtures with paired uncertainty intervals clustered by fixture/date. Secondary: calibration bins, league and season slices, draw performance, missingness, latency and pipeline reliability. Market benchmark uses *genuine timestamped odds* only, removes margin; otherwise `NOT_AVAILABLE`. Accuracies and simulated ROI are secondary diagnostics, NOT promotion criteria. A changed model is a candidate only if it clears a predeclared practical improvement threshold and uncertainty test on untouched holdout and cannot be explained by leakage, leakage-prone sources, selection or data quality. Holdout is assessed once per frozen candidate. After promotion, use separate real-time immutable shadow trials. No betting recommendation follows automatically.

## Execution guard
Do not modify directories `forward_morning_263/`, `forward_quad_263/`, `experiments/263/`, existing .github workflows or immutable SHA seals as part of research import. Keep raw fetched data out of git; commit only manifests, code, unit tests and small provenance-safe summaries. No branch merges into the running 2.6.3 without explicit separate review.

## Current status
- [x] Dedicated branch created from `experiment/263-toplu-karsilastirma`
- [x] Sources and experimental rules recorded
- [ ] Historical ingestion run and coverage QA on actual downloaded files
- [ ] Independent competitor implementations and chronological paired test
- [ ] One frozen summary; engineering promotion decision
