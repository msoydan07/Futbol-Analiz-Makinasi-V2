# Future head-to-head: 2.6.3 vs independent challengers

**Decision recorded:** the existing 2.6.3 and sealed pilot remain untouched.
No historical XGBoost result may be treated as if it was a sealed historical
2.6.3 forecast. The already-viewed 2025+ scores are EXPLORATORY.

## Synchronized identity contract
A valid comparison row needs:
- Same verified `fixture_id`, home/away team identities and competition.
- Exactly the same fixture start time and country-local timezone.
- Every contender created before kickoff and timestamped `as_of_utc`.
- Same pre-match information cutoff: known results before `as_of_utc`;
  lineup/injury/odds only if verified and available to both models before cutoff.
- Independent 2.6.3 SHA-locked forecast as written; **never recomputed**.
- Challenger forecast generated before kickoff on the research branch, SHA-
  sealed separately. Research-side predictions may be published externally,
  but **must not enter** the original 2.6.3 cohort or affect original selections.
- One verified official full-time result, attached after the match. Compare
  multiclass 1X2 vectors only; other markets await their own experiment.
- Missing model, bad team mapping, unverified fixture or different cutoffs:
  `NOT_COMPARABLE` with explicit reason, not an imputed probability.

## Prospective test policy
Before any new fixtures: freeze challengers' feature definitions, weights,
calibration, parameters, model binaries, source snapshots and output schema.
Results-only training is not equivalent to richer 2.6.3 data: compare both as
different information budgets and report this limitation.

Pre-register a minimum sample target (proposed >= 300 common matches over
multiple weekends and leagues, with the final power calculation written
before kickoff), primary multiclass log loss, secondary multiclass Brier,
paired differences and uncertainty grouped by date/league. Do not force a
winner on a small sample. Repeat weekly without changing candidate weights,
recording *all eligible fixtures*, including failures and missing forecasts.

For simple fixed hybrid, weights are exactly (Elo 1/3, Poisson 1/3,
XGBoost 1/3), unoptimized on the viewed period. If its constituent predictions
are not generated from pre-kickoff, frozen features, score it as `PAS`.

The historical 20-league archive is a modeling resource, not proof of
profitable wagers. No retrospective bookmaker quote is fabricated.
Promotion requires a separate engineering review and cannot be inferred
from one prospective week.
