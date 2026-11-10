"""Three distinct 6/7/8 November date blocks: original pre-match seals only.

6 Nov legacy quad4 and 7 Nov acceptance3 are NOT promoted into new100.
8 Nov 39-match report is referenced without rescoring.
Original forecast files/data, production M4 and calibration remain immutable.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from datetime import timedelta
from research.opponent_goals.nov7_sealed_date_block_263 import (
    ROOT, Blocked, load, sha256_object, aware, proper_probability, bin_metrics,
    summarize, evaluate as evaluate_nov7
)
DAY = "2026-11-06"
EVIDENCE = "research/opponent_goals/nov6_primary_score_evidence_20261110.json"
REGISTRY = "experiments/263/evidence/identity_index_263.json"
HOSTS = {
    "TUR1": {"www.tff.org"}, "ITA1": {"www.legaseriea.it"},
    "NED1": {"www.knvb.nl"}, "FRA1": {"www.toulousefc.com"}
}
MARKETS = ("BTTS_YES", "OVER_1.5", "OVER_2.5", "OVER_3.5")

def evaluate(root=ROOT, *, evidence_override=None):
    root=Path(root)
    evidence = evidence_override if evidence_override is not None else load(root,EVIDENCE)
    reg=load(root, REGISTRY)
    if (evidence.get("schema")!="263_NOV6_PRIMARY_SOURCE_OBSERVATIONS_OLD_QUAD4_RESEARCH_V1"
            or evidence.get("day")!=DAY
            or evidence.get("cohort")!="legacy_forward_quad4_NOT_acceptance3_or_new100"
            or evidence.get("ci_independently_rechecks_sources") is not False
            or evidence.get("production_result_attestation") is not False
            or len(evidence.get("observations",[]))!=4):
        raise Blocked("INVALID_LEGACY_QUAD4_RESEARCH_CONTRACT")
    if (reg.get("payload_sha256")!=sha256_object({k:v for k,v in reg.items() if k!="payload_sha256"})
            or not isinstance(reg.get("aliases"),dict)):
        raise Blocked("ORIGINAL_TEAM_REGISTRY_TAMPERED")
    per_market={m:[] for m in MARKETS}
    done=[]
    seen_paths=set()
    seen_matches=set()
    for row in evidence["observations"]:
        path=row.get("seal_path","")
        key=(row["league"],row["home"],row["away"])
        if (path in seen_paths or key in seen_matches
                or not re.fullmatch(r"forward_quad_263/2026-11-06/[a-f0-9]{24}\.json",path)):
            raise Blocked("INVALID_OR_DUPLICATE_LEGACY_SEAL")
        seen_paths.add(path);seen_matches.add(key)
        parsed=urlsplit(row["source_url"])
        if (parsed.scheme!="https" or parsed.hostname not in HOSTS.get(row["league"],set())
                or not parsed.path or parsed.username or parsed.password or parsed.port):
            raise Blocked("OUTCOME_PRIMARY_SOURCE_MISMATCH")
        if row.get("source_type") not in ("OFFICIAL_LEAGUE","OFFICIAL_CLUB","OFFICIAL_FEDERATION"):
            raise Blocked("OUTCOME_PROVENANCE_NOT_ACCEPTED")
        y=row["score"]
        if (not isinstance(y,list) or len(y)!=2 or
                any(type(x) is not int or not 0<=x<=20 for x in y)):
            raise Blocked("INVALID_FULL_TIME_SCORE")
        sealed=load(root,path)
        digest=sha256_object({k:v for k,v in sealed.items() if k!="payload_sha256"})
        if (sealed.get("schema")!="quad_forward_263_v1"
                or digest!=sealed.get("payload_sha256")
                or digest!=row.get("seal_sha256")):
            raise Blocked("FORECAST_SHA_CHANGED_OR_UNMATCHED")
        fx=sealed["fixture"]
        if (fx["match_local_date"]!=DAY or fx["league"]!=row["league"]
                or fx["home_id"]!=reg["aliases"].get(row["home"])
                or fx["away_id"]!=reg["aliases"].get(row["away"])
                or fx["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE"):
            raise Blocked("FORECAST_TEAM_ID_OR_OFFICIAL_FIXTURE_MISMATCH")
        created,checked,kickoff=(aware(sealed["created_at_utc"]),
                                aware(fx["source_checked_at_utc"]),
                                aware(fx["kickoff_utc"]))
        if not(created<kickoff and checked<kickoff and checked<=created+timedelta(seconds=60)):
            raise Blocked("LEGACY_SEAL_IS_NOT_PREMATCH")
        if (sealed["data"]["research_shadow_unverified_source"] is not False or
                sealed["data"]["snapshot_sha256"]!="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"):
            raise Blocked("TRAINING_HISTORY_CHANGED")
        model=sealed.get("model_predictions",{}).get("M4",{})
        if model.get("status")!="AVAILABLE":
            raise Blocked("M4_NOT_AVAILABLE")
        m=model["goals"]["markets"]
        ms=m["1X2"]
        if set(ms)!={"H","D","A"} or abs(sum(proper_probability(p) for p in ms.values())-1)>1e-5:
            raise Blocked("MS_PROBABILITY_SAFETY_GUARD")
        h,a=y
        truth={"BTTS_YES":int(h>0 and a>0),
               "OVER_1.5":int(h+a>=2),"OVER_2.5":int(h+a>=3),
               "OVER_3.5":int(h+a>=4)}
        row_metrics={}
        for market in MARKETS:
            x=bin_metrics(m[market],truth[market])
            per_market[market].append(x)
            row_metrics[market]={"p":round(x["p"],6),"y":x["y"]}
        done.append({"league":row["league"],"home":row["home"],"away":row["away"],
                     "score":y,"forecast_sha256":digest,"source_url":row["source_url"],
                     "markets":row_metrics})
    old=evaluate_nov7(root)
    if old["nov7"]["n"]!=3 or old["nov8_reference_only"]["n"]!=39:
        raise Blocked("OLD_DATE_BLOCK_CHANGED")
    return {
      "schema":"263_THREE_SEPARATE_PREMATCH_DATE_BLOCKS_NOV6_7_8_V1",
      "nov6":{"cohort":"legacy_forward_quad4","n":4,
              "source_class":"PRIMARY_WEB_PAGES_MANUALLY_REVIEWED_NOT_CI_ATTESTED",
              "markets":{k:summarize(v) for k,v in per_market.items()},
              "matches":done},
      "nov7":old["nov7"],"nov8_reference_only":old["nov8_reference_only"],
      "distinct_match_dates":3,
      "research_event_count_UNPOOLED":46,
      "all_cohorts_separate":True,
      "M4_parameters_unchanged":True,
      "accepted_4518_history_unchanged":True,
      "official_results_new100_promoted":0,
      "production_calibration_changed":False,
      "candidate_promoted":False,
      "decision":"HOLD_NEED_NEW_BLIND_AND_INDEPENDENT_MATCH_DATES",
      "limitations":[
        "Only 6 Nov four legacy, 7 Nov three acceptance3 and 8 Nov 39 new100 research: NOT ONE UNIFORM PILOT",
        "8 Nov report is read unchanged; 6/7 public webpages were reviewed externally, not fetched anew in CI",
        "No official provider row rights gate or federation ID attestation is made here",
        "Three dates with 4/3/39 matches cannot justify 60-70 pct bucket correction, odds/EV or M4 promotion",
        "New results required from later pre-match SHA seals for genuine prospective calibration"]
    }

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="");o=p.parse_args()
    report=evaluate()
    if o.output:
        Path(o.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"schema":report["schema"],"dates":report["distinct_match_dates"],
                      "n_by_day":{"2026-11-06":4,"2026-11-07":3,"2026-11-08":39},
                      "decision":report["decision"]},ensure_ascii=False))
    print(json.dumps(report["nov6"]["markets"],ensure_ascii=False))
