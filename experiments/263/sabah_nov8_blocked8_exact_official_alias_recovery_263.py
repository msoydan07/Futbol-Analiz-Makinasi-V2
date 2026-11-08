"""One-pass Nov8 recovery for EXACTLY eight blocked official 2026-27 league fixtures.

No pilot, no price, no bookmaker, no changes to B/C2/C3/M4 or historical files.
Official league fixture source and canonical membership verification mandatory.
"""
from __future__ import annotations
import argparse, json, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_batch_263 import named
from sabah_named_source_acceptance_263 import named_only_runner
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from forward_c3 import valid_gate
from market_fifth_baseline_263 import sealed_payload
from sabah_today_scope_readonly_263 import summarize

DAY="2026-11-08"
TR=ZoneInfo("Europe/Istanbul")
FROZEN="experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json"
HISTORY="data/quad_accepted_263/extended_history.csv"
BASE="m4_quad_base/historical_results.csv"
AUDIT="data/quad_accepted_263/source_acceptance.json"
M4LOCK="experiments/263/m4_lock.json"
DEV="experiments/263/forward_dev_calibration_lock_263.json"
TARGETS={
    ("GER1","1. FC Köln","Bayer Leverkusen"),
    ("ESP1","Celta Vigo","Levante"),
    ("ESP1","Atlético Madrid","Barcelona"),
    ("NED1","FC Utrecht","NEC Nijmegen"),
    ("POR1","Vitória Guimarães","FC Porto"),
    ("POR1","Rio Ave","Braga"),
    ("BEL1","Union Saint-Gilloise","Genk"),
    ("BEL1","Sint-Truiden","Zulte Waregem"),
}
# Official-site labels from league and club pages, not fuzzy guesses.
ALIASES={
 "GER1":{"Bayer Leverkusen":"Bayer 04 Leverkusen"},
 "ESP1":{"Celta Vigo":"Celta","RC Celta":"Celta",
         "Atlético Madrid":"Atlético de Madrid",
         "FC Barcelona":"FC Barcelona","Barcelona":"FC Barcelona"},
 "NED1":{"NEC Nijmegen":"N.E.C. Nijmegen",
         "N.E.C.":"N.E.C. Nijmegen"},
 "POR1":{"Vitória Guimarães":"Vitória SC","Braga":"SC Braga"},
 "BEL1":{"Union Saint-Gilloise":"Royale Union Saint-Gilloise",
         "Sint-Truiden":"STVV","Zulte Waregem":"SV Zulte Waregem"}
}
def registry_name(league,name):
    return ALIASES.get(league,{}).get(name,name)

def canon_gate(league,home,away,lookup_override=None):
    # Gate still checks 2026/27 immutable registry, official source and kickoff.
    # Convert ONLY reviewed exact aliases in the already-verified official
    # observation and user manifest, never create a fixture from alias alone.
    if lookup_override is None:
        return {"status":"NOT_VERIFIED","reason":"OFFICIAL_OBSERVATION_REQUIRED"}
    def observed(h,a):
        result=lookup_override(h,a)
        if not isinstance(result,dict) or result.get("status")!="VERIFIED_OFFICIAL_FIXTURE":
            return result
        converted=dict(result)
        converted["display_home_before_exact_alias"]=result.get("home")
        converted["display_away_before_exact_alias"]=result.get("away")
        converted["home"]=registry_name(league,result["home"])
        converted["away"]=registry_name(league,result["away"])
        return converted
    return named_only_runner(league,registry_name(league,home),
                             registry_name(league,away),lookup_override=observed)

def run():
    now=datetime.now(timezone.utc)
    if now.astimezone(TR).date().isoformat()!=DAY:
        raise ValueError("ONLY_NOV8_NO_BACKDATING")
    all42=named("legacy96",DAY,FROZEN)
    if len(all42)!=42:raise ValueError("PINNED_42_CHANGED")
    rows=[r for r in all42 if (r["league"],r["home"],r["away"]) in TARGETS]
    if len(rows)!=8 or len(set((r["league"],r["home"],r["away"]) for r in rows))!=8:
        raise ValueError("ONLY_ORIGINAL_EIGHT_ALLOWED")
    gateway=OfficialFixtureGateway(gate_runner=canon_gate)
    original=gateway.resolve_id
    def resolve(league,name):
        return original(league,registry_name(league,name))
    gateway.resolve_id=resolve
    from forward_quad import predict_quad_from_verified_gate
    from forward_empirical_baseline_263 import produce
    from four_model_value_policy_263 import decide
    lock=json.loads(Path(DEV).read_text(encoding="utf-8"))
    results=[]
    with tempfile.TemporaryDirectory(prefix="263_8_exact_official_") as temp:
        for row in rows:
            league,home,away=row["league"],row["home"],row["away"]
            item=dict(row,status="PENDING",research_only=True)
            try:
                gate=gateway.lookup(league,home,away)
                item["source_evidence"]=gateway.latest_match_evidence(league,home,away)
                if gate.get("status")!="VERIFIED":
                    item.update(status="BLOCKED_SOURCE_OR_CANONICAL",reason=gate.get("reason"))
                else:
                    instant=datetime.now(timezone.utc)
                    _,_,_,ko,_,_=valid_gate(gate,instant)
                    item["official_kickoff_utc"]=ko.isoformat()
                    if ko.astimezone(TR).date().isoformat()!=DAY or instant+timedelta(minutes=2)>=ko:
                        item.update(status="BLOCKED_KICKOFF_PASSED_OR_WRONG_DATE")
                    else:
                        path,forecast=predict_quad_from_verified_gate(
                            gate,HISTORY,Path(temp),M4LOCK,now=instant,
                            base=BASE,source_audit=AUDIT)
                        sealed_payload(forecast,"quad_forward_263_v1")
                        baseline=produce(forecast,HISTORY,now=instant)
                        decision=decide(forecast,baseline,lock,observation=None,now=instant)
                        if decision.get("status")!="RESEARCH_PAS":raise ValueError("ONLY_PAS_NO_ODDS")
                        item.update(summarize(forecast,decision,
                                          "TEMPORARY_READONLY_EXACT_OFFICIAL_ALIAS_RECOVERY"))
                if item["status"]!="EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE":
                    entry=gateway._get(league)
                    item["official_page_events_today"]=[
                        {"home":e.get("home"),"away":e.get("away"),
                         "match_date":e.get("match_date"),"kickoff_utc":e.get("kickoff_utc")}
                        for e in entry.get("events",[])
                        if e.get("match_date")==DAY]
            except (ValueError,OSError,KeyError,TypeError,AssertionError) as e:
                item.update(status="BLOCKED_DATA_OR_MODEL",
                            reason=type(e).__name__+":"+str(e)[:190])
            results.append(item)
    return {
        "schema":"263_NOV8_EIGHT_EXACT_OFFICIAL_ALIAS_NONPILOT_V1",
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "day_turkey":DAY,"original_blocked_eight":8,
        "actual_model_outputs":sum(r["status"]=="EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE" for r in results),
        "no_new_pilot_records":True,"bookmaker_calls":0,
        "historical_and_model_files_unchanged":True,
        "research_only":True,"items":results}
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",required=True)
    args=a.parse_args()
    result=run()
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"total":8,"models":result["actual_model_outputs"],
                      "blocked":[[r["league"],r["home"],r["away"],r["status"],r.get("reason")]
                                 for r in result["items"] if r["status"]!="EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE"],
                      "new_pilot":0,"odds_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
