"""READ ONLY inventory of 21 Nov 2026 50 signed football forecasts.

Verification only. Never edit a decision, fixture, model, outcome or seal.
Outputs structured 50-row report for later separately sourced post-match scoring.
"""
import json,glob,hashlib,sys
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]
DST=Path("/tmp/nov21_fifty_frozen_inventory.json")
TR=ZoneInfo("Europe/Istanbul")
DATE="2026-11-21"

def hash_payload(d):
    return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,
       separators=(",",":"),allow_nan=False).encode("utf8")).hexdigest()

def utc(v):
    t=datetime.fromisoformat(v.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("NAIVE_DATE")
    return t.astimezone(timezone.utc)

def check(d):
    old=d.get("payload_sha256")
    if old!=hash_payload({k:v for k,v in d.items() if k!="payload_sha256"}):
        raise ValueError("CORRUPT_RECORD_SHA")

def main():
    reg=json.loads((ROOT/"experiments/263/evidence/identity_index_263.json").read_text())
    team={k:v["name"] for k,v in reg["teams"].items()}
    paths=sorted((ROOT/"experiments/263/sabah_research/new100"/DATE).glob("*/decision.json"))
    assert len(paths)==50, f"EXPECTED_50_FROZEN_DECISIONS_GOT_{len(paths)}"
    seen=set();records=[]
    for path in paths:
        decision=json.loads(path.read_text());check(decision)
        fx=decision["fixture"]
        token=path.parent.name
        forecast_path=ROOT/"forward_morning_263"/DATE/(token+".json")
        baseline_path=path.with_name("baseline.json")
        forecast=json.loads(forecast_path.read_text());check(forecast)
        baseline=json.loads(baseline_path.read_text());check(baseline)
        assert forecast["payload_sha256"]==decision["forecast_sha256"]==baseline["forecast_sha256"]
        assert fx==forecast["fixture"]
        kickoff=utc(fx["kickoff_utc"]);created=utc(forecast["created_at_utc"])
        baseline_utc=utc(baseline["created_at_utc"])
        assert created<=baseline_utc<kickoff, f"NOT_PREMATCH_{token}"
        if (baseline["last_result_date"]>=DATE
            or baseline["source_snapshot_sha256"]!=forecast["data"]["snapshot_sha256"]):
            raise ValueError("HISTORY_DATE_OR_SNAPSHOT_LEAKAGE")
        if (fx["match_local_date"]!=DATE
            or fx["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE"):
            raise ValueError("UNEXPECTED_DATE_OR_LIVE_FIXTURE_SOURCE")
        pair=(fx["league"],fx["home_id"],fx["away_id"])
        if pair in seen:raise ValueError("DUPLICATE_FIXTURE")
        seen.add(pair)
        if decision["status"]!="RESEARCH_CANDIDATE_NOT_APPROVED":
            raise ValueError("PILOT_CANDIDATE_RESEARCH_STATUS_NOT_APPROVED")
        main=decision["main_candidate"];alt=decision["alternative_candidate"]
        if main is None or alt is None:raise ValueError("MISSING_MAIN_OR_ALT")
        vectors={x["market"]:x["calibrated_probability"] for x in decision["model_market_diagnostics"]}
        expected={"MS1","MSX","MS2","BTTS_YES","BTTS_NO","OVER_2.5","UNDER_2.5"}
        if set(vectors)!=expected or len(decision["model_market_diagnostics"])!=7:
            raise ValueError("SEVEN_EVENTS_INCOMPLETE_OR_DUPLICATE")
        for group in [("MS1","MSX","MS2"),("BTTS_YES","BTTS_NO"),
                      ("OVER_2.5","UNDER_2.5")]:
            if abs(sum(vectors[k] for k in group)-1)>0.00000001:
                raise ValueError("SEVEN_MARKET_PROBS_NOT_NORMALIZED")
        if main["calibrated_probability"]!=max(vectors.values()) or vectors[main["market"]]!=main["calibrated_probability"]:
            raise ValueError("MAIN_CHANGED_FROM_HIGHEST_SEVEN_EVENT")
        if vectors[alt["market"]]!=alt["calibrated_probability"]:
            raise ValueError("ALTERNATIVE_NOT_FROM_SIGNED_SEVEN_EVENT")
        if main["family"]==alt["family"]:
            raise ValueError("ALTERNATIVE_MUST_BE_DIFFERENT_FAMILY")
        rec={"league":fx["league"],"home":team.get(fx["home_id"]), "away":team.get(fx["away_id"]),
             "kickoff_utc":fx["kickoff_utc"],"kickoff_tr":kickoff.astimezone(TR).strftime("%H:%M"),
             "main_market":main["market"],"main_prob":main["calibrated_probability"],
             "main_expert":main["anchor_model"],"seven_model_probabilities":vectors,
             "alt_market":alt["market"],
             "alt_prob":alt["calibrated_probability"],"alt_expert":alt["anchor_model"],
             "model_selection_version":decision["selection_policy_version"],
             "status":decision["status"],"betting_authorized":decision["betting_authorized"],
             "forecast_sha256":forecast["payload_sha256"],"decision_sha256":decision["payload_sha256"],
             "baseline_sha256":baseline["payload_sha256"],
             "forecast_created_at_utc":forecast["created_at_utc"],
             "forecast_created_before_KO":created<kickoff,
             "official_source_url":fx["official_source"],
             "decision_path":str(path.relative_to(ROOT)),
             "token":token}
        if rec["home"] is None or rec["away"] is None:
            raise ValueError("UNKNOWN_ID_IN_FROZEN_RECORD")
        records.append(rec)
    archives=sorted((ROOT/"experiments/263/second_pdf_commentary_archive_263"/DATE).glob("*.json"))
    observed=[]
    for path in archives:
        if path.name=="index.json":continue
        d=json.loads(path.read_text())
        if d.get("record_sha256")!=hash_payload({k:v for k,v in d.items() if k!="record_sha256"}):
            raise ValueError("ARCHIVE_SHA_INVALID")
        m=d.get("original_seal",{})
        if not any(z["decision_sha256"]==m.get("decision_sha256") for z in records):
            raise ValueError("ARCHIVED_SECOND_PDF_CANNOT_FIND_ORIGINAL_DECISION")
        observed.append({"fixture":d["match"],"decision_sha256":m["decision_sha256"],
                         "archived_second_pdf_sha256":d.get("source_pdf_fingerprints",{}).get("second_pdf_sha256"),
                         "archival_kind":d.get("record_kind"),
                         "recorded_at_utc":d.get("recorded_at_utc")})
    result={"schema":"NOV21_50_PREMATCH_FROZEN_SHA_AUDIT_V1",
           "date_tr":DATE,"cohort":"NEW100_20261121",
           "count":len(records),
           "status":"READONLY_VERIFIED_50_SHA_NOT_SCORED",
           "official_betting_authorized_count":sum(x["betting_authorized"] for x in records),
           "same_model_version":len(set(x["model_selection_version"] for x in records))==1,
           "second_pdf_comments_count":len(observed),
           "source_note":"SOURCE IS EXISTING GITHUB COMMITTED FORECASTS FROM 21 NOV. NO POSTMATCH REWRITE.",
           "predictions":sorted(records,key=lambda x:(x["league"],x["kickoff_utc"],x["home"])),
           "second_pdf_observations":observed}
    result["report_sha256"]=hash_payload(result)
    DST.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print("NOV21_INVENTORY_SUMMARY",json.dumps({
        "decision_count":len(records),"market_counts":dict(Counter(x["main_market"] for x in records)),
        "leagues":dict(Counter(x["league"] for x in records)),
        "second_pdf_archived":len(observed),
        "all_shas_valid":True,
        "earliest_utc":min(x["forecast_created_at_utc"] for x in records),
        "latest_utc":max(x["forecast_created_at_utc"] for x in records),
        "report_sha256":result["report_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
