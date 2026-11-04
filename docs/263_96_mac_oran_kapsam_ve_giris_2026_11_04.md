# 2.6.3 96-match odds coverage + manual pre-kickoff intake — 4 November 2026

**Engineering decision:** Do NOT modify B/C2/C3/M4, S1/S2 thresholds, frozen archive, 96-fixture cohort or main. Prices are a fifth *reference*, not a fifth calibrated model.

## Coverage facts (2026-11-04 public check)

- Nesine public iddaa bulletin lists 1/X/2, Over/Under 2.5 and BTTS Yes/No columns, as well as league/date. https://www.nesine.com/iddaa/futbol . **This does not prove that a public programmatic endpoint exists, nor that all 96 matches are available at T−60**, nor that displayed prices were actually timestamped.
- iddaa.com has public program pages but no authenticated developer / bookmaker feed was approved: https://www.iddaa.com/program/canli . DO NOT parse a pre-existing live page as proof of a pre-match quote.
- API alternative: The Odds API documents soccer market coverage, but its historical endpoint is paid; bookmaker/10-league-specific coverage must be verified before any purchase: https://the-odds-api.com/liveapi/guides/v4/ ; https://the-odds-api.com/sports-odds-data/sports-apis.html .
- Separate TheOddsAPI.com/BettingDataAPI service claims many football leagues but some soccer BTTS access has a narrower documented scope; not accepted as a replacement for required Turkish bookmakers: https://api.theoddsapi.com/docs .
- **Do not place automated bets, submit credentials, bypass rate limiting, or scrape private endpoints.**

## Audit of prerequisites

Current branch `experiment/263-toplu-karsilastirma` has a static 96-candidate fixture list, mathematical scoring for B/C2/C3/M4, no-vig benchmark and a postmatch fifth-reference scorer.

However, the repo tree at time of inspection had **NO** `data/quad_accepted_263/extended_history.csv`, `data/quad_accepted_263/source_acceptance.json`, `forward_quad_263/*.json` or `market_quotes_locked/*.json`. Therefore 96 future quotes or real pre-KO model records cannot yet be claimed. The existing source-acceptance gate is essential and is NOT bypassed.

## Stage A — now implemented

- `market_quote_intake_263.py`: accepts a NEW user-created request **only if a genuine pre-KO, SHA-verifiable `forward_quad_263` record already exists**. All request attributes must be manually observed from an actual source (only approved iddaa / Nesine / Bilyoner / Maçkolik domains); quote is not fetched by code.
- Quotes must have the EXACT complete and synchronized 1/X/2 and/or KG Yes/No and/or 2.5 Under/Over market. Validator calls EXISTING `classification_odds_263.odds_evidence`; no duplicate calculation or rate adjustment. Max 10 minutes since manual source observation; GitHub action and both timestamps must be before KO; missing/old/wrong priced groups are BLOCKED.
- Writes exactly one append-only SHA-256 sealed `263_manual_market_snapshot_v1` tied to the locked `quad_forward_263_v1` SHA; repeats are denied. Blocked events are preserved in a separate report. The existing `market_fifth_baseline_263.py` can score this data against final scores later without model changes.
- Price data remains **HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED**; the downstream field `verification=INDEPENDENTLY_CHECKED` is an attestation input expected by the old interface, NOT independently checked by the code. GitHub user/commit-time and source authenticity still require an independent audit. No A/B/C status or S2 betting authorization is generated.
- New workflow only reacts to ADDED JSON price request files; not old model or historic data. One isolated test suite protects date, identity, full counter prices, modification attempts and existing paired scoring.
- Source order policy remains iddaa.com > Nesine > Bilyoner > Maçkolik. Only use a lower-priority source if the preferred source cannot be reliably observed at the analysis time; record why. Do not search best-looking prices retrospectively.

## Stage B — necessary before 6–8 November

1. **FIRST** get the current completed 2026/27 data snapshot independently human accepted and official fixture verified, so `forward_quad_263` can generate real pre-KO locks. Without this, quote-intake workflow appropriately refuses to create records.
2. Observe the actual bookmaker page around T−60. If any prices captured manually, add a brand-new JSON to `experiments/263/market_quote_requests/` using the README instructions. Do not create a fake request just to make CI green.
3. Before KO check the GitHub bot commit of the quote lock and model lock; compare fixture/time/source hash. Any missing evidence => `NOT_EVALUABLE`, not a synthetic record.
4. If too few markets are accessible, provide a 10-league coverage table of `MS`, `KG`, `2.5` observed vs missing; **NO S2** without complete contemporaneous prices and independent calibration.
5. Update no odds values after kickoff. Keep `raw vs model` comparison descriptive; no production rollout based on 3 calendar days.

## Stage C — Monday 9 November

96 fixed candidates → official fixture verified → sealed eligible four-model predictions N → manual complete odds observations N_price per market → scored matched N_final. Report logloss / Brier for bookmaker-derived no-vig vs B/C2/C3/M4 on **exact same fixtures**. Report data gaps by league and source; include S1/S2 only if truly sealed beforehand. Three dates cannot support date-block bootstrap requiring >=10 dates.

No automatic source feed is installed or promised. No real-money betting claim, guarantee of profits, or model promotion.
