"""Read-only historical pre-UEFA-date domestic input coverage for accepted 132.
No fixture network, no model fitting, no strength coefficients, no pilot.
"""
import argparse,csv,hashlib,json
from datetime import date
from collections import Counter
from pathlib import Path

SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
SCHEMA="263_UEFA_2025_26_BOTH_TEN_LEAGUES_UNION_COVERAGE_V1"
OUT=Path("data/europe_staged_263/2025_26_asof_strength_input")
class AuditError(ValueError):pass

def load_inputs(history,union):
    raw=Path(history).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise AuditError("DOMESTIC_ARCHIVE_SHA_MISMATCH")
    reader=csv.DictReader(raw.decode("utf-8-sig").splitlines())
    cols={"league","season","match_date","home_id","away_id","home_goals","away_goals","result"}
    if not reader.fieldnames or not cols.issubset(reader.fieldnames):
        raise AuditError("DOMESTIC_REQUIRED_FIELDS_MISSING")
    domestic=[]
    for r in reader:
        try:r["_date"]=date.fromisoformat(r["match_date"])
        except (ValueError,TypeError):raise AuditError("DOMESTIC_DATE_INVALID")
        if not r["home_id"] or not r["away_id"] or r["home_id"]==r["away_id"]:
            raise AuditError("DOMESTIC_CLUB_ID_INVALID")
        domestic.append(r)
    if len(domestic)!=4413:raise AuditError("DOMESTIC_ARCHIVE_SIZE_MISMATCH")
    u=json.loads(Path(union).read_text(encoding="utf8"))
    if u.get("schema")!=SCHEMA or u.get("status")!="REVIEW_ONLY_TRAINING_FORBIDDEN":
        raise AuditError("PREVIOUS_UNION_STATUS_NOT_REVIEW_ONLY")
    rows=u.get("matches")
    if not isinstance(rows,list) or len(rows)!=132:
        raise AuditError("UNION_132_CANDIDATES_MISSING")
    if Counter(x.get("competition") for x in rows)!=Counter({"UEFA_CL":95,"UEFA_EL":37}):
        raise AuditError("UNION_95_37_SPLIT_MISMATCH")
    for r in rows:
        if r.get("model_training_allowed") is not False or r.get("identity_link_status")!="REVIEW_ONLY_NOT_OFFICIAL_UEFA_NUMERIC_ID":
            raise AuditError("UNION_UNAPPROVED_IDENTITY_MUST_NOT_PROMOTE")
        if r.get("season")!="2025-2026":raise AuditError("UNION_WRONG_SEASON")
    return domestic,rows

def xg_pair(r):
    try:
        h,a=float(r.get("home_xg") or "nan"),float(r.get("away_xg") or "nan")
        return 0<=h<=10 and 0<=a<=10
    except (TypeError,ValueError):return False

def measure(domestic,uefa):
    result=[];counts={}
    for fixture in uefa:
        day=date.fromisoformat(fixture["date"])
        by_team={}
        for side in ("home","away"):
            tid=fixture[side+"_club_id_candidate"];league=fixture[side+"_league"]
            pre=[r for r in domestic
                 if r["season"]=="2025-2026" and r["league"]==league
                 and r["_date"]<day and tid in (r["home_id"],r["away_id"])]
            by_team[side]={"league":league,"prior_match_count":len(pre),
                           "prior_xg_pair_count":sum(xg_pair(r) for r in pre),
                           "last_prior_date":max((r["match_date"] for r in pre),default=None)}
        c=counts.setdefault(fixture["competition"],Counter())
        c["matches"]+=1
        both4=all(by_team[s]["prior_match_count"]>=4 for s in ("home","away"))
        both8=all(by_team[s]["prior_match_count"]>=8 for s in ("home","away"))
        bothxg=all(by_team[s]["prior_xg_pair_count"]>=4 for s in ("home","away"))
        c["both_4_prior_goals"]+=both4
        c["both_8_prior_goals"]+=both8
        c["both_4_prior_xg_pairs"]+=bothxg
        c["under_4_at_least_one_team"]+=not both4
        result.append({"competition":fixture["competition"],"date":fixture["date"],
                       "home_candidate_id":fixture["home_club_id_candidate"],
                       "away_candidate_id":fixture["away_club_id_candidate"],
                       "asof_domestic_matches":by_team,"both_4_goals":both4,
                       "both_8_goals":both8,"both_4_xg_pairs":bothxg,
                       "uefa_numeric_ids_verified":False,
                       "original_source_available_at_that_historical_time_verified":False,
                       "model_eligible":False})
    summary={"schema":"263_UEFA_ASOF_DOMESTIC_INPUT_COVERAGE_V1",
      "candidate_matches":len(result),
      "per_competition":{k:dict(v) for k,v in counts.items()},
      "historical_domestic_source_sha256":SHA,
      "rule":"Only domestic league results dated strictly before UEFA date, no same-day results",
      "data_compiled_later_not_proof_of_pre_kickoff_source_retrievability":True,
      "UEFA_numeric_club_identity_verified":False,
      "historical_real_time_data_availability_verified":False,
      "strength_model_fitted":False,"xg_model_fitted":False,
      "pilot_or_main_changed":False,"model_training_allowed":False}
    return summary,result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",required=True);p.add_argument("--union",required=True)
    args=p.parse_args()
    dom,uefa=load_inputs(args.history,args.union)
    summary,records=measure(dom,uefa)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"coverage.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    (OUT/"matches_REVIEW_ONLY.json").write_text(json.dumps(
        {"schema":summary["schema"],"training_allowed":False,"matches":records},
        ensure_ascii=False,indent=2)+"\n")
    print("UEFA_ASOF_COVERAGE="+json.dumps(summary,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
