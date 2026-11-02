# 2.6.3 decision preparation / odds A-B-C / 2 Nov 2026

Status: provisional ONLY. Old C2 decision_preflight and all four model engines unchanged.
No predictions saved, no model promoted, no official A/B/C and no betting authorized.

- A candidate: >=75% with sufficient source/model, robust ±10% lambda stress >=70%.
- B candidate: independently verified, pre-match, same-source/time/market counterpart odds;
  expected value >=5% and no-vig edge >=3 percentage points; sufficient source/model.
- A+B both, C is significant watch; missing data -> NOT EVALUABLE, not a fabricated C.
- Odds alone cannot alter a model's probability. No-vig is proportional normalization
  using all mutually exclusive counter-prices. Overlapping 1X/X2/12 are NOT normalized
  against one another. Price source verification cannot be inferred from a JSON flag.
- Numerical example only, not a real quote: p=70%, odds=1.60 -> break-even=62.5%, EV=12%.
  Without corresponding other bookmaker prices no no-vig edge and B cannot be approved.
- Current numerical engines' historical calibration is not independently forward accepted.
  This isolated module therefore always returns official_class=null and betting=false.
- Tuesday (3 Nov 2026) source staging workflow is on main because GitHub schedules
  require default branch. It updates experimental STAGED data only, never the locked
  historical archive, accepted input, main model or pilot forecast journal.
