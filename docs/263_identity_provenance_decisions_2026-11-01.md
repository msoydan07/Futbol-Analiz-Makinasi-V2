# 2.6.3 historical identity/source bridge — 2026-11-01

**Scope:** frozen historical identity linkage, NOT live fixture/squad validation. The old `identity.py`, `verify_match_on_demand.py` and team alias resolver were NOT rewritten.

- Source: workflow run 41251343847, artifact 13061725424 (2026-10-31).
- Historical results: 4,413, 10 leagues, two seasons. SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Same artifact registry: 215 canonical teams, 370 aliases, 4,413 fixtures. SHA-256 `c7d31ea3a039e926e72c4a87806d7675384d6a2deeadc86f8ab7ded35e9fda98`.
- All 4,413 historical `fixture_id/league/season/date/home_id/away_id` matched; no identity mismatch. 215 official-name flags in registry were recorded previously; **NOT independently checked now**.
- Registry artifact is NOT committed at `data/match_registry.json`: provide frozen artifact file explicitly. Do not invent/resolve aliases on the fly.
- Added `identity_provenance_263.py`, 10 adversarial tests, 4 bridge tests; existing integrated offline report optionally accepts pinned registry and emits `OFFLINE_REGISTRY_LINKAGE_VALIDATED`, never `VERIFIED_OFFICIAL_FIXTURE`.
- SHA mismatch, UUID mismatch, fixture/team mismatch fail closed. When no registry is supplied report says `NOT_CHECKED`.
- Local batch including existing software tests: **61 tests passed**, plus one read-only 4,413-row snapshot linkage check and one hypothetical offline CLI smoke run.
- No model change, no new historical performance run, no live-match records, no bets, no EV and no pilot.

### Usage

```sh
python experiments/263/integrated_offline_report.py \
  --history historical_results.csv \
  --evidence experiments/263/evidence/acceptance_263.json \
  --registry match_registry.json \
  --registry-sha256 c7d31ea3a039e926e72c4a87806d7675384d6a2deeadc86f8ab7ded35e9fda98 \
  --cases hypothetical_cases.json \
  --out-json audit.json --out-markdown audit.md
```

**Open:** independent official fixture/time and lineup source checks, injury/suspension and tactical provenance still NOT_CHECKED. Do not promote these from stored URLs or claims. Only isolated experiment branch is modified.
