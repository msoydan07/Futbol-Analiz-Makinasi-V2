"""Single requested match -> live official lookup -> identity gate -> data audit.
Does not require a bulk fixture CSV or trigger Module 0.
Usage: python analyze_named_match_gate.py TUR1 "Galatasaray" "Konyaspor"
"""
import importlib
import json
import sys
from verify_match_on_demand import verify_named_match

LOOKUPS={
 "ENG1":"premier_league_fixture_lookup",
 "ENG2":"championship_fixture_lookup",
 "GER1":"bundesliga_fixture_lookup",
 "ESP1":"laliga_fixture_lookup",
 "ITA1":"serie_a_fixture_lookup",
 "FRA1":"ligue1_fixture_lookup",
 "NED1":"eredivisie_fixture_lookup",
 "TUR1":"besiktas_official_fixture_lookup",
 "POR1":"portugal_fixture_lookup",
 "BEL1":"belgium_fixture_lookup",
}
def run(league,home,away,lookup_override=None,registry_path="data/match_registry.json"):
 if league not in LOOKUPS:
  return {"status":"REJECTED","reason":"unsupported_league"}
 try:
  lookup=lookup_override or importlib.import_module(LOOKUPS[league]).lookup
  observed=lookup(home,away)
 except Exception as exc:
  return {"status":"NOT_VERIFIED","reason":"official_lookup_error","detail":str(exc)[:160]}
 if not isinstance(observed,dict) or observed.get("status")!="VERIFIED_OFFICIAL_FIXTURE":
  return {"status":"NOT_VERIFIED","reason":"official_match_not_confirmed","observation":observed}
 # A successful observation must identify the requested participants, not just a kickoff.
 from identity import normalize
 try:
  if normalize(observed.get("home"))!=normalize(home) or normalize(observed.get("away"))!=normalize(away):
   return {"status":"NOT_VERIFIED","reason":"official_observation_teams_mismatch"}
 except (ValueError,TypeError):
  return {"status":"NOT_VERIFIED","reason":"official_observation_teams_missing"}
 # Only a successfully fetched and parsed official observation can enter the identity gate.
 checked=verify_named_match(league,home,away,observed.get("kickoff_utc"),
                            observed.get("source_url"),observed.get("retrieved_at_utc"),
                            source_checked=True,registry_path=registry_path)
 if checked.get("status")=="VERIFIED":
  checked["next_step"]="COLLECT_AND_VALIDATE_2_6_2_INPUTS"
  checked["first_xi_required"]=False
 return checked

if __name__=="__main__":
 if len(sys.argv)!=4:raise SystemExit("Usage: python analyze_named_match_gate.py LEAGUE HOME AWAY")
 result=run(*sys.argv[1:])
 print(json.dumps(result,ensure_ascii=False,indent=2))
 sys.exit(0 if result.get("status")=="VERIFIED" else 1)
