"""Single requested match -> live official lookup -> identity gate -> data audit.
Does not require a bulk fixture CSV or trigger Module 0.
Usage: python analyze_named_match_gate.py TUR1 "Galatasaray" "Konyaspor"
"""
import importlib
import json
import sys
from verify_match_on_demand import verify_named_match
from identity import Registry

LOOKUPS={
 "ENG1":"premier_league_fixture_lookup",
 "ENG2":"championship_fixture_lookup",
 "GER1":"bundesliga_fixture_lookup",
 "ESP1":"laliga_fixture_lookup",
 "ITA1":"serie_a_fixture_lookup",
 "FRA1":"ligue1_fixture_lookup",
 "NED1":"eredivisie_fixture_lookup",
 "TUR1":"tff_fixture_lookup",
 "POR1":"portugal_fixture_lookup",
 "BEL1":"belgium_fixture_lookup",
}
def _variants(registry, team_id, requested):
 """Only known names attached to the SAME immutable team ID; no fuzzy guessing."""
 from identity import normalize
 names = [requested, registry.data["teams"][team_id]["name"]]
 names += sorted((alias for alias, tid in registry.data["aliases"].items()
                  if tid == team_id), key=lambda s: (len(s), s))
 out = []
 seen = set()
 for name in names:
  token = normalize(name)
  if token not in seen:
   seen.add(token)
   out.append(name)
 return out[:4]


def run(league,home,away,lookup_override=None,registry_path="data/match_registry.json"):
 """Maçkolik spelling -> registry IDs -> SAME IDs in independently parsed official match.

 Does not build a fixture list or treat Maçkolik as official fixture evidence.
 The existing official adapter must really fetch and parse the corresponding match.
 """
 if league not in LOOKUPS:
  return {"status":"REJECTED","reason":"unsupported_league"}
 try:
  from team_name_resolver import resolve as resolve_team_name
  reg=Registry(registry_path)
  home_id=resolve_team_name(reg,league,home)
  away_id=resolve_team_name(reg,league,away)
  if home_id==away_id:
   return {"status":"REVIEW_REQUIRED","reason":"identical_club_ids"}
  # If a current-season historical membership registry exists, avoid linking a
  # club from another league. A stored prior fixture is NOT future fixture proof.
  registered=[v for v in reg.data.get("fixtures",{}).values()
              if v.get("league")==league and v.get("season")]
  if registered:
   latest=max(v["season"] for v in registered)
   members={v.get(role) for v in registered if v.get("season")==latest
            for role in ("home_id","away_id")}
   if home_id not in members or away_id not in members:
    return {"status":"REVIEW_REQUIRED","reason":"team_not_in_current_league_registry"}
  lookup=lookup_override or importlib.import_module(LOOKUPS[league]).lookup
  homes=_variants(reg,home_id,home)
  aways=_variants(reg,away_id,away)
 except (KeyError,ValueError,OSError,TypeError,ImportError) as exc:
  return {"status":"REVIEW_REQUIRED","reason":"team_identity_not_resolved","detail":str(exc)[:150]}

 combos=sorted(((i,j) for i in range(len(homes)) for j in range(len(aways))),
               key=lambda ij:(max(ij),abs(ij[0]-ij[1]),sum(ij)))[:8]
 diagnostics=[]
 for i,j in combos:
  try:
   observed=lookup(homes[i],aways[j])
  except Exception as exc:
   diagnostics.append("official_lookup_error:"+type(exc).__name__)
   continue
  if not isinstance(observed,dict) or observed.get("status")!="VERIFIED_OFFICIAL_FIXTURE":
   diagnostics.append(str(observed.get("reason","not_verified"))[:60] if isinstance(observed,dict) else "bad_official_observation")
   continue
  try:
   # Neither text equality nor Maçkolik naming is official match verification.
   # The official parser may echo requested names; its own fetched source
   # verification must have succeeded before returning VERIFIED_OFFICIAL_FIXTURE.
   oh=resolve_team_name(reg,league,observed["home"])
   oa=resolve_team_name(reg,league,observed["away"])
   if (oh,oa)!=(home_id,away_id):
    return {"status":"NOT_VERIFIED","reason":"official_match_identity_mismatch"}
  except (KeyError,ValueError,TypeError):
   return {"status":"NOT_VERIFIED","reason":"official_observed_names_unmapped"}
  checked=verify_named_match(league,home,away,observed.get("kickoff_utc"),
                             observed.get("source_url"),observed.get("retrieved_at_utc"),
                             source_checked=True,registry_path=registry_path)
  if checked.get("status")=="VERIFIED":
   if checked.get("home_id")!=home_id or checked.get("away_id")!=away_id:
    return {"status":"NOT_VERIFIED","reason":"registry_identity_disagreement"}
   checked["next_step"]="COLLECT_AND_VALIDATE_2_6_3_INPUTS"
   checked["first_xi_required"]=False
   checked["input_name_source"]="MACKOLIK_USER_SUPPLIED_NAMES"
   checked["official_lookup_attempts"]=len(diagnostics)+1
  return checked
 return {"status":"NOT_VERIFIED","reason":"official_match_not_confirmed",
         "official_lookup_attempts":len(combos),
         "source_diagnostics":sorted(set(diagnostics))[:5]}

if __name__=="__main__":
 if len(sys.argv)!=4:raise SystemExit("Usage: python analyze_named_match_gate.py LEAGUE HOME AWAY")
 result=run(*sys.argv[1:])
 print(json.dumps(result,ensure_ascii=False,indent=2))
 sys.exit(0 if result.get("status")=="VERIFIED" else 1)
