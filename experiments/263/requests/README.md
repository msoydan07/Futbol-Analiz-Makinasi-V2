# Request queue (user-named fixtures only)

Add one **new** JSON file per requested batch, never edit an existing file.
Path: `experiments/263/requests/20261101_example.json` (example name only; do not create unless user names matches).

```json
{
  "schema": "c3_named_match_batch_request_v1",
  "matches": [
    {"league": "TUR1", "home": "HOME_TEAM_NAME", "away": "AWAY_TEAM_NAME"}
  ]
}
```

The example is NOT a verified fixture. Do not add matches on the assistant's initiative.
The request cannot supply a kickoff, data, odds, team ID, or fabricated official gate.
New request commit triggers precisely one batch action. Existing requests are never replayed.
A blocked attempt produces an honest failure/evidence report instead of a forecast.
No Model B change, no Modül 0, no first-half corner, no automatic wager or EV.
