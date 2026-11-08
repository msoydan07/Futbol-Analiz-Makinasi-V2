"""Read-only pre-kickoff identity/timing bridge between a research seal and
the immutable 2.6.3 pilot. No evaluation metrics, stakes or fabricated results.

This tool returns PAS if either side was not actually sealed before kickoff.
It does NOT produce challenger predictions and does not certify the supplied
official fixture URL. External source verification is a separate requirement.
"""
import argparse,json
from datetime import timedelta
from pathlib import Path
from prospective_seal import dt,digest,SCHEMA

class NotComparable(ValueError): pass

def join(original,research,*,max_cutoff_gap_minutes=15):
    if original.get("schema")!="quad_forward_263_v1":
        raise NotComparable("WRONG_263_SCHEMA")
    if research.get("schema")!=SCHEMA:
        raise NotComparable("WRONG_RESEARCH_SCHEMA")
    checksum=research.get("payload_sha256")
    if not checksum or checksum!=digest({k:v for k,v in research.items()
                                         if k!="payload_sha256"}):
        raise NotComparable("RESEARCH_SHA_CHANGED")
    # The original forecast SHA must be checked against its own historical
    # canonical hash convention, not a new custom re-serialization here.
    from hashlib import sha256
    canonical=json.dumps({k:v for k,v in original.items() if k!="payload_sha256"},
        ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf8")
    expected=sha256(canonical).hexdigest()
    if original.get("payload_sha256")!=expected:
        raise NotComparable("ORIGINAL_SHA_CHANGED")
    fx=original["fixture"]
    rf=research["candidate"]["fixture"]
    for field in ("league","home_id","away_id"):
        if fx[field]!=rf[field]:
            raise NotComparable("DIFFERENT_FIXTURE_"+field)
    if dt(fx["kickoff_utc"])!=dt(rf["kickoff_utc"]):
        raise NotComparable("DIFFERENT_KICKOFF")
    kickoff=dt(fx["kickoff_utc"])
    orig_created=dt(original["created_at_utc"])
    challenger_created=dt(research["candidate"]["created_at_utc"])
    if not orig_created<kickoff or not challenger_created<kickoff:
        raise NotComparable("LATE_FORECAST")
    gap=abs(orig_created-challenger_created)
    if gap>timedelta(minutes=max_cutoff_gap_minutes):
        raise NotComparable("DIFFERENT_INFORMATION_CUTOFF")
    if original["model_predictions"].get("M4",{}).get("status")!="AVAILABLE":
        raise NotComparable("INCUMBENT_M4_UNAVAILABLE")
    p=original["model_predictions"]["M4"]["goals"]["markets"]["1X2"]
    if abs(sum(p.values())-1)>1e-6 or set(p)!={"H","D","A"}:
        raise NotComparable("INCUMBENT_INVALID_PROBABILITY")
    return {
        "status":"PAIRED_IDENTITY_AND_TIMING_ONLY",
        "league":fx["league"],"home_id":fx["home_id"],
        "away_id":fx["away_id"],"kickoff_utc":fx["kickoff_utc"],
        "original_forecast_sha":original["payload_sha256"],
        "challenger_forecast_sha":checksum,
        "original_asof":original["created_at_utc"],
        "challenger_asof":research["candidate"]["created_at_utc"],
        "asof_gap_minutes":gap.total_seconds()/60,
        "m4":p,
        "challengers":research["candidate"]["models"],
        "not_result_verified":True,
        "not_market_calibrated":True,
        "betting_authorized":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True)
    p.add_argument("--research",required=True)
    args=p.parse_args()
    with open(args.original,encoding="utf8") as f:orig=json.load(f)
    with open(args.research,encoding="utf8") as f:res=json.load(f)
    try:
        print(json.dumps(join(orig,res),ensure_ascii=False,indent=2))
    except NotComparable as err:
        print(json.dumps({"status":"NOT_COMPARABLE","reason":str(err)}))

if __name__=="__main__":main()
