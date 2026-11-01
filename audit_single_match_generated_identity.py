"""Audit that the generated registry and historical rows share immutable IDs."""
import csv,json
from pathlib import Path
from identity import Registry
from single_match_model_b import analyze

def main():
 root=Path("data")
 registry_file=root/"match_registry.json"
 history_file=root/"historical_results.csv"
 if not registry_file.is_file() or not history_file.is_file():
  raise SystemExit("Missing generated registry/history; run historical data pipeline first")
 registry=Registry(registry_file)
 with history_file.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 if not rows:raise SystemExit("Historical results empty")
 teams=registry.data["teams"];fixtures=registry.data["fixtures"]
 missing=[r["fixture_id"] for r in rows if r["home_id"] not in teams or r["away_id"] not in teams or r["fixture_id"] not in fixtures]
 if missing:raise SystemExit("History identity mismatch: "+str(missing[:5]))
 if len({r["fixture_id"] for r in rows})!=len(rows):raise SystemExit("Duplicate fixture IDs")
 latest=max(r["match_date"] for r in rows)
 candidates=[r for r in rows if r["match_date"]==latest]
 sample=candidates[0]
 prediction=analyze(rows,sample["league"],sample["home_id"],sample["away_id"],"2027-06-01")
 if prediction["status"] not in ("READY","INSUFFICIENT_HISTORY"):raise SystemExit("Unexpected model status")
 report={"status":"PASS","historical_matches":len(rows),"registry_teams":len(teams),"registry_fixtures":len(fixtures),"identity_mismatches":0,"sample_model_status":prediction["status"],"note":"Historical identity audit only; not a verified future fixture"}
 (root/"single_match_identity_integration_audit.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report))
if __name__=="__main__":main()
