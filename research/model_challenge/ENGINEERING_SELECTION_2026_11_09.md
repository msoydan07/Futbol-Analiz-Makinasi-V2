# ENGINEERING SELECTION — 2026-11-09

## Selected challenger for match result (1-X-2): **XGBoost v1**

**Decision type:** A frozen research challenger selection based on historical evidence.
**Not** a claim that it beats production 2.6.3/M4, or that it has bookmaker edge.
**No deploy/merge into 2.6.3 or replacement of other markets.**

## Evidence used for model selection
A. Same 4,331 previously viewed historical fixtures across 20 leagues,
2025/26 segment:
- Elo log loss 1.002005, Brier 0.598378
- Poisson log loss 1.002710, Brier 0.598902
- XGBoost log loss 0.997560, Brier 0.595040
- Fixed equal-weight hybrid log loss 0.996379, Brier 0.594339
- Hybrid vs XGBoost paired log-loss difference -0.00118;
  date-block 95% interval [-0.00391,+0.00172] overlaps 0.
- XGBoost beats Elo by log loss in 10/20 individual leagues;
  hybrid beats XGBoost in 11/20. Main weakness: draw overprediction
  (XGBoost 25.70% mean predicted vs 21.43% observed draws).

B. Additional **chronologically later** 2026/27 period using **frozen parameters**
and an OpenFootball commit pinned before this assessment (through 2026-09-22),
covering 441 scored matches across 8 leagues:
- Elo 0.993107 log loss / 0.593591 Brier
- Poisson 0.993676 / 0.592798
- XGBoost **0.980450 / 0.584530**
- Equal-weight hybrid 0.984910 / 0.587349
- For this check, XGBoost was trained only on the previous seasons;
  it was not tuned or trained on 2026/27 labels.
- The 8-league coverage and data source snapshot are narrower than
  the 20-league historical archive; uncertainty and data quality remain.
  No time-stamped odds or original 2.6.3 same-fixture forecasts are available.

## Decision logic
A marginally better log loss of the fixed hybrid on the earlier viewed
period does not justify an extra deployment dependency because the
hybrid-vs-XGBoost uncertainty includes zero and the later, strictly
chronological 441-match check favored XGBoost on *both* proper losses.
Consequently **choose one** candidate for the experimental 1-X-2 model:
XGBoost v1. The challenger hyperparameters are frozen:
max_depth=3, n_estimators=210, learning_rate=0.025,
min_child_weight=20, reg_lambda=10, reg_alpha=1,
subsample=0.85, colsample_bytree=0.9, random_state=263.
No score-based switching by league or fixture; Elo, Poisson and hybrid
remain baseline research references, not live alternatives.
The selected model is not a full-market replacement.

## Next required actions before *ready for live use* can be stated
1. Create an inference-only pipeline from a pinned, licensed, complete
   current-season source, with real fixtures verified independently.
   The existing historical XGBoost evaluation uses *played* match rows,
   not future fixture predictions; passing unknown future final scores
   to an evaluation script would be a safety/accuracy error.
2. Freeze serialized trained model and the input feature schema;
   encode as-of time, training cutoff and fixture verification.
3. Run prospective shadow inference and SHA sealing; fail closed when
   source freshness or team mapping cannot be verified.
4. On the same actual fixture as 2.6.3's frozen M4, compare predicted
   1-X-2 only after official result verification, once the predeclared
   sample is adequate. The 2.6.3 prediction engine and its other markets
   remain unchanged until this independent review.
5. Evaluate any future odds only with verifiable pre-kickoff snapshots;
   no claim of betting profitability based on these results.

## Status labels
RESEARCH_1X2_CHALLENGER_SELECTED: **YES — XGBOOST_V1**
MAIN_2_6_3_REPLACED: **NO**
LIVE_INFERENCE_END_TO_END_VERIFIED: **NO**
PROSPECTIVE_M4_HEAD_TO_HEAD_COMPLETE: **NO**
GAMBLING_EDGE_PROVEN: **NO**

## GitHub evidence
- Source archive: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42532602610
- Independent four-way stress: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42535756855
- Newer-season frozen-parameter check: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42535896258
