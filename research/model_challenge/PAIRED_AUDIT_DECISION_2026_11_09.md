# Model Challenge — paired diagnostic decision, 2026-11-09

## Confirmed execution
- Pinned historical source archive: 18,255 scored fixtures, 20 league codes, 2022/23–2025/26 partial coverage; source run 42532602610.
- Elo baseline: run 42532664152.
- Predeclared Poisson challenger: run 42533012701.
- XGBoost challenger (fixed dev-optimized hyperparameters): run 42533506784.
- Strict common-fixture audit: run 42533823323 (completed successfully).
- Original 2.6.3 and SHA-sealed future cohorts were **not modified**.

## Common evaluation set (4,331 fixtures)
| Method | 1X2 top-one accuracy | Multiclass log loss | Multiclass Brier | Predicted draw | Actual draw |
| --- | ---: | ---: | ---: | ---: | ---: |
| Elo | 0.52436 | 1.00201 | 0.59838 | 0.25239 | 0.21427 |
| Poisson | 0.51789 | 1.00271 | 0.59890 | 0.24201 | 0.21427 |
| XGBoost | 0.51466 | 0.99756 | 0.59504 | 0.25698 | 0.21427 |

Lower loss is better; top-one accuracy is a different objective from calibrated probability quality.

## Paired date-block bootstrap (challenger minus baseline, 95% interval)
- XGBoost − Elo log loss: −0.00445 [−0.00877, −0.00032].
- XGBoost − Elo Brier: −0.00334 [−0.00620, −0.00062].
- XGBoost − Poisson log loss: −0.00515 [−0.01051, −0.00031].
- XGBoost − Poisson Brier: −0.00386 [−0.00757, −0.00060].
- Poisson − Elo log loss: +0.00070 [−0.00414, +0.00553].

This is exploratory inference from a **previously viewed** period. These confidence intervals do not erase repeated-analysis/model-selection bias or provider quality issues; they cannot independently qualify promotion. Draw calibration is imperfect for all models. League-level slices and exact scores are in the run artifact `model-challenge-league-paired-diagnostics`.

## Engineering gate
**NO PROMOTION / NO BETTING EDGE CLAIM / NO INCUMBENT PERFORMANCE CONCLUSION.**

The 2.6.3 B/C2/C3/M4 frozen forecast series uses a different set of source-gated fixtures, history and prediction cutoffs. It cannot be fairly compared to these retrospective 4,331 fixtures by lining up aggregate error rates. Do not reconstruct a claimed *historically sealed* 2.6.3 forecast from results-only archive. As-of synchronized predictions for the same future fixtures would be required.

Next bounded experiments:
1. Audit league slices, potential match timestamp and duplicate-team mapping defects, and draw calibration by season. Do not retune on the viewed evaluation period.
2. Implement independent hybrid candidate from frozen deterministic development-only rules and inspect on a truly unviewed dataset or future shadow cohort. Any attempt to tune or select the hybrid on 2025+ data is leakage by design.
3. Include true time-stamped bookmaker odds only after source rights and quote timing verification; no odds means ROI/profitability unavailable.
4. Future live test: separate immutable research forecasts on identical fixtures for 2.6.3 and challengers; protect original pilot and avoid cash stakes.
