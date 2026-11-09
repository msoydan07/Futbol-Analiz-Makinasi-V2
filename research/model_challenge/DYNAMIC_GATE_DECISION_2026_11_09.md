# Match-specific M4/XGBoost gate — experiment decision (2026-11-09)

## Question
Does a learned per-fixture probability weight between M4 and XGBoost
improve 1X2 probability quality, compared with either expert or a
simple fixed-weight average?

## Implemented
- A feature-only logistic gating formula based on each expert's
  pre-match confidence, entropy, draw probability and disagreement.
- Causal retrospective OOF expert pairs on 2025/26 historical records:
  **435** same-fixture pairs on predeclared date windows.
- Trained gate once on those 435 pairs.
- Compared on **441 different 2026/27 matches** (eight available leagues)
  already reconstructed in the previous M4/XGBoost research audit.
- Same M4 code and frozen lock, no modification to 2.6.3.

## Results, 441 comparable matches
| Model | Multiclass log loss (lower better) | Multiclass Brier (lower better) |
|---|---:|---:|
| M4 | 0.995186 | 0.592002 |
| XGBoost | **0.980450** | **0.584530** |
| Fixed 50/50 M4+XGBoost | 0.982490 | 0.585469 |
| Learned dynamic gate | 0.982776 | 0.585629 |

Learned weight on M4: **0.5200 to 0.5217** across 441 fixtures;
average 0.52146. Practically constant. No evidence that it has learned
a meaningful *match-specific* selection rule. Relative to pure
XGBoost, the learned gate was worse on both proper scores. Confidence
interval of the paired log-loss difference gate minus XGBoost is
[-0.00689, +0.01151] and crosses zero.

## Engineering decision
**REJECT this meta-gate candidate for deployment.** It adds complexity
but did not outperform the simpler XGBoost model. The previous choice
XGBoost v1 remains the provisional **MS 1X2 challenger**, not a
replacement for the existing production 2.6.3/M4 engine.

Do not retune 435-pair gate to improve scores on the already-viewed 441
fixtures. Additional gate methods may be researched only if they use
distinct causal OOF training and a genuinely unseen evaluation window,
or are explicitly labeled exploratory. Neither the separate historical
reconstruction nor this experiment can prove positive betting expected
value. All other markets (goal lines/BTTS) remain 2.6.3-owned.

## Evidence
- GitHub workflow: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42566658017
- Artifact: `model-challenge-dynamic-gate-diagnostics`
- Code: `research/model_challenge/build_meta_oof.py`,
  `meta_gate.py`, `evaluate_meta_gate.py`
- Archive cohort 2026/27 is already observed / not a new blind set;
  probabilities are retrospective recreations and not SHA-sealed
  original production forecasts.

## Status
- M4/XGBoost research OOF pair training: DONE
- Dynamic gating experiment: DONE
- Learned match-by-match expert superiority: **NOT DEMONSTRATED**
- Current chosen XGBoost research challenger: UNCHANGED
- Existing 2.6.3 production or pilot mutated: NO
- Full end-to-end future inference: NOT YET VERIFIED
