# FINAL ENGINEERING CHECKPOINT — 2.6.3 TEN LEAGUE MS (2026-11-09)

## Evidence and scope
Only the owner's SHA-accepted, canonical-ID 4,518-match history was
used. SHA256: 1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9.
This is a limited research acceptance, NOT independent verification of
every score.

XGBoost V1 hyperparameters are frozen and fitted to 2025/26 records only.
M4 uses the *original unchanged* m4_integrated.py with frozen lock
360d/4/48. Both systems reconstruct strictly past-only historical
predictions. Neither uses actual sealed 2.6.3 morning artifact forecasts.

### Test A — first league matchdate per ISO week, common match-date cutoff
187 paired fixtures, one unpaired:
- M4 accuracy 52.94%, log loss 1.02079, Brier 0.61266
- XGBoost accuracy 49.73%, log loss 1.02204, Brier 0.61104
- Fixed M4/XGBoost 50/50 accuracy 50.80%, log loss 1.01675, Brier 0.60811
- XGB-minus-M4 date-bootstrap 95% interval [-0.02313, +0.02594]

### Test B — all eligible 2026/27 fixtures, SAME WEEKLY cutoff for both
985 scored 2026/27 fixtures, 896 eligible paired, 89 excluded
(88 insufficient archived team history, 1 M4 lambda unavailable).
Models frozen every league-week Monday: no within-week results used
by either expert. Fairer identical information set, less up-to-date
than the actual match-morning 2.6.3 system.
- M4 accuracy **53.35%**, log loss 0.99173, Brier 0.59071
- XGBoost accuracy 51.12%, log loss 1.00101, Brier 0.59715
- Fixed 50/50 accuracy 53.13%, log loss **0.99021**, Brier **0.58978**
- XGB-minus-M4 ISO-week clustered 95% interval [-0.00939,+0.02944].
The slight blend logloss/Brier improvement is not separately established
as statistically significant in this protocol.

These are TWO RELATED retrospectives sharing the same score source and
season, NOT independent tests. This historical period has been inspected
in previous research, and only a limited feature set is available.
No inference of expected betting profitability is supported.

## Engineering decision
**Keep current M4 / existing 2.6.3 unchanged for production.**
It has better 1X2 top-choice accuracy than the XGBoost candidate on
the large shared-week 896-fixture evaluation and is comparable on
proper probability scores. The blend has a **small exploratory**
probability-score advantage, insufficient to replace an incumbent.
XGBoost remains a *research-only shadow challenger*. A match-by-match
learned expert gate was also tested and rejected (no proof of benefit).

**This is a real model decision, not a request to wait for more
matches before any engineering choice.** Select M4 for existing
2.6.3, preserve XGBoost V1 as fixed challenger, do not add a fragile
model selector or blend without stronger unseen validation.

## GitHub evidence
- Limited research snapshot SHA audit:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42568207243
- First date-of-week matched 187:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42568880153
- Broad identical weekly-cutoff matched 896:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42569098553
- New source connection blocked identity mapping (no silent errors):
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42567999656
- Canonical-history XGB synthetic end-to-end inference:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42568461375

## Remaining practical work
- Daily *genuinely updated* source and verified next-fixture input before
  first real XGBoost research shadow; historical arşiv latest 2026-11-03.
- Persist actual forecast to repository (local SHA file alone is not a
  durable tamper-evident remote record).
- Official result post-match evaluation on paired sealed forecasts.
- The main M4's existing goal/BTTS markets are outside this 1X2 check
  and entirely unchanged.
