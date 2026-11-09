# XGBoost V1 – pre-kickoff research inference (2026-11-09)

## What is implemented and verified
- `xgb_live_inference.py` consumes **played results** and a **separately official-verified** future fixture manifest. The fixture input has **no goals or result** fields.
- Same 25 input features as `xgb_challenger.make_features`, proved with synthetic date-causal parity tests.
- Chronological historical training with frozen development-selected XGBoost V1 hyperparameters (depth=3, 210 trees, learning rate=0.025, min_child_weight=20; same fixed regularization/seed).
- Rejects: unknown league/team identity, insufficient history/warmup, duplicate or future scores, stale fixture/history, missing official verification marker, kickoff in past or too near, invalid probabilities.
- Preserves verified `fixture_id`, `home_id`, `away_id` for future paired comparison with M4. Does not invent IDs from club names.
- Produces `XGBoost` MS H-D-A only, marks Elo/Poisson/hybrid explicitly **PAS**. The existing `prospective_seal.py` independently validates and writes a SHA-sealed, append-only research record (never overwrites).
- All tests use *synthetic fixture/score data* and prove technical validation, not the truth of any external sports source.

## Run command
```bash
python research/model_challenge/xgb_live_inference.py \
  --history /verified_asof/results.csv \
  --fixture /verified_official_gate/fixture.json \
  --out /tmp/xgb_v1_candidate.json \
  --seal-root /tmp/xgb_shadow_seals
```
Run only from the dedicated research branch. Candidate manifest schema:
```json
{
  "schema": "MC_VERIFIED_FIXTURE_INPUT_V1",
  "fixture_id": "provider-verified-id",
  "league": "ENG1",
  "home_name": "Exact historical archive team name",
  "away_name": "Exact historical archive team name",
  "home_id": "2.6.3 verified home ID",
  "away_id": "2.6.3 verified away ID",
  "kickoff_utc": "2026-11-16T17:00:00+00:00",
  "official_fixture_url": "https://example.org/actual-official-fixture-page",
  "source_verified_at_utc": "2026-11-16T09:00:00+00:00",
  "history_asof_utc": "2026-11-16T08:00:00+00:00",
  "fixture_verified_by": "EXTERNAL_OFFICIAL_GATE"
}
```
This is **schema illustration only**, not a real fixture or verification.
The mere string `EXTERNAL_OFFICIAL_GATE` is NOT cryptographic evidence
the external official source has been verified. The actual fixture gate and
provenance chain must be checked independently before real use.

## Not done / blockers
1. No current-season licensed, audited, sufficiently fresh history source
   connected to this runner: the pinned OpenFootball research snapshot
   ends September 22, 2026, and should fail the November freshness gate.
2. Independent official fixture verification and trusted identity mapping
   into this manifest remain external manual/connector inputs. This
   workflow does **not** scrape or invent a future match.
3. No actual upcoming fixture has been processed and sealed in this
   development stage. Only synthetic end-to-end tests have run.
4. No 2.6.3 production mutation, merge or market replacement.
5. This is a research 1X2 model pipeline, not a full-market engine,
   and no odds-edge, guaranteed accuracy or profitability is established.

## Verified action
- CI: `Model challenge - pre-kickoff XGBoost inference QA`
- Successful synthetic end-to-end inference+SHA-seal run:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42567282642

## Next engineering step
Integrate with a genuinely verified fixture gate and current as-of results
snapshot, document licensing and completeness, then run a pre-kickoff live
research-only shadow for the exact same fixture as unmodified M4.
