"""Separate, quarantine-only UEFA CL/EL candidate lane for 2.6.3.

No online fetch or independent verification, no domestic historical merge,
no model selection, no predictions, no odds, no A/B/C, no pilot ledger.
"""
import argparse,json,re,hashlib
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA="263_UEFA_CL_EL_STAGED_ONLY_v1"
COMPETITIONS={"UEFA_CL":"uefachampionsleague","UEFA_EL":"uefaeuropaleague"}
STAGES={"QUALIFYING","LEAGUE_PHASE","KNOCKOUT","FINAL"}
class UEFAStageError(ValueError):pass

def aware(value,field):
    if not isinstance(value,str):raise UEFAStageError(field+"_TIME_REQUIRED")
    try:t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:raise UEFAStageError(field+"_TIME_INVALID") from exc
    if t.tzinfo is None or t.utcoffset() is None:
        raise UEFAStageError(field+"_TIMEZONE_REQUIRED")
    return t.astimezone(timezone.utc)

def source_id(competition,url):
    if competition not in COMPETITIONS:raise UEFAStageError("UNSUPPORTED_COMPETITION")
    if not isinstance(url,str):raise UEFAStageError("SOURCE_MISSING")
    u=urlsplit(url)
    if u.scheme!="https" or u.netloc.lower() not in ("uefa.com","www.uefa.com") or u.query or u.fragment:
        raise UEFAStageError("SOURCE_NOT_UEFA")
    pat=r"/"+COMPETITIONS[competition]+r"/match/([0-9]{5,12})--[a-z0-9-]+/?"
    match=re.fullmatch(pat,u.path)
    if not match:raise UEFAStageError("UEFA_MATCH_LINK_INVALID")
    return match.group(1)

def candidate(record,asof):
    if not isinstance(record,dict):raise UEFAStageError("RECORD_MUST_BE_OBJECT")
    required={"competition","season","round","home","away","source_url",
              "kickoff","observed_at","result_status","neutral_venue"}
    allowed=required|{"home_goals","away_goals"}
    if not required.issubset(record) or set(record)-allowed:
        raise UEFAStageError("CANDIDATE_FIELDS_INVALID")
    competition=record["competition"]
    official_id=source_id(competition,record["source_url"])
    if record["season"]!="2026-2027":raise UEFAStageError("SEASON_NOT_SUPPORTED")
    if record["round"] not in STAGES:raise UEFAStageError("ROUND_NOT_SUPPORTED")
    home=record["home"];away=record["away"]
    if not all(isinstance(x,str) and x.strip() and len(x)<=120 for x in (home,away)) or home.strip().casefold()==away.strip().casefold():
        raise UEFAStageError("INVALID_CLUB_NAMES")
    if type(record["neutral_venue"]) is not bool:raise UEFAStageError("NEUTRAL_VENUE_FLAG_REQUIRED")
    kickoff=aware(record["kickoff"],"KICKOFF");seen=aware(record["observed_at"],"OBSERVED")
    if seen>asof:raise UEFAStageError("FUTURE_OBSERVATION")
    if record["result_status"] not in ("SCHEDULED","FINAL"):
        raise UEFAStageError("STATUS_INVALID")
    hg=record.get("home_goals");ag=record.get("away_goals")
    if record["result_status"]=="FINAL":
        if not (type(hg) is int and type(ag) is int and 0<=hg<=40 and 0<=ag<=40):
            raise UEFAStageError("PARTIAL_OR_INVALID_RESULT")
        if kickoff>=seen or kickoff>=asof:raise UEFAStageError("RESULT_BEFORE_KICKOFF")
        state="CLAIMED_FINAL_PENDING_SOURCE_VERIFICATION"
    else:
        if hg is not None or ag is not None:raise UEFAStageError("UNPLAYED_HAS_SCORE")
        state="FUTURE_SCHEDULED_CANDIDATE" if kickoff>asof else "PAST_UNRESOLVED_CANDIDATE"
    return {"id":"UEFA:"+official_id,"uefa_match_id":official_id,
            "competition":competition,"season":"2026-2027","round":record["round"],
            "home_uefa_name":home.strip(),"away_uefa_name":away.strip(),
            "domestic_home_id":None,"domestic_away_id":None,
            "crosswalk_status":"MANUAL_IDENTITY_REVIEW_REQUIRED",
            "kickoff_utc":kickoff.isoformat(),"neutral_venue":record["neutral_venue"],
            "result_state":state,"home_goals":hg,"away_goals":ag,
            "source_url":record["source_url"],"observed_at_utc":seen.isoformat(),
            "source_status":"UEFA_MATCH_LINK_FORMAT_ONLY_NOT_INDEPENDENTLY_FETCHED",
            "model_eligible":False,"A_B_C_approved":False,"pilot_recorded":False}

def stage(matches,as_of):
    asof=aware(as_of,"ASOF")
    if not isinstance(matches,list) or len(matches)>2000:raise UEFAStageError("BATCH_INVALID")
    visited=set();items=[]
    for record in matches:
        r=candidate(record,asof)
        if r["uefa_match_id"] in visited:raise UEFAStageError("DUPLICATE_UEFA_MATCH_ID")
        visited.add(r["uefa_match_id"]);items.append(r)
    items.sort(key=lambda x:(x["kickoff_utc"],x["id"]))
    return {"schema":SCHEMA,"status":"EUROPE_UNVERIFIED_CANDIDATE_STAGING",
            "fixtures":items,
            "audit":{"as_of_utc":asof.isoformat(),
                     "counts":{c:sum(r["competition"]==c for r in items) for c in COMPETITIONS},
                     "verified_match_count":0,
                     "verified_training_result_count":0,
                     "official_page_actually_fetched":False,
                     "domestic_10_leagues_unchanged":True,
                     "four_model_forecasts_allowed":False,
                     "ABC_allowed":False,"pilot_recorded":False}}

def main(argv=None):
    p=argparse.ArgumentParser(description="UEFA CL/EL candidates separate from 10 league pipeline")
    p.add_argument("--input",required=True)
    p.add_argument("--as-of",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args(argv)
    path=Path(args.input)
    if not path.is_file() or path.stat().st_size>2_000_000:raise UEFAStageError("INPUT_INVALID")
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or set(obj)!={"matches"}:raise UEFAStageError("ONLY_MATCHES_INPUT")
    result=stage(obj["matches"],args.as_of)
    output=Path(args.output)
    if Path("data/europe_staged_263") not in output.parents or output.suffix!=".json":
        raise UEFAStageError("ONLY_EUROPE_STAGED_OUTPUT_ALLOWED")
    output.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    output.write_text(serialized,encoding="utf-8")
    print(json.dumps({"status":result["status"],"candidates":len(result["fixtures"]),
                      "sha256":hashlib.sha256(serialized.encode()).hexdigest(),
                      "verified":False,"pilot":False}))
if __name__=="__main__":main()
