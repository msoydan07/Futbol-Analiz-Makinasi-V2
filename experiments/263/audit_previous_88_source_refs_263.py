"""Non-promoting 88-match corroboration audit using source-round web references.

All 88 independent visible-source score values were manually transcribed from
public web result pages into manifest. Their origin remains human/AI-transcribed
and is NOT a separately archived raw web source, nor proof of human acceptance.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE_SHA="35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1"
PRIOR_SHA="279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8"
NEW_SHA="69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14"
EXPECTED_BY_LEAGUE={"BEL1":9,"ENG1":9,"ENG2":12,"ESP1":9,"FRA1":8,
                    "GER1":9,"ITA1":8,"NED1":9,"POR1":7,"TUR1":8}
SCHEMA="263_88_previous_score_web_round_reference_v1"


def check(path,sha,length):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha: raise ValueError("PINNED_DATA_SHA_MISMATCH:"+str(path))
    with Path(path).open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=length or len({r["fixture_id"] for r in rows})!=len(rows):
        raise ValueError("DATA_COUNT_OR_DUPLICATE_ID:"+str(path))
    return {r["fixture_id"]:r for r in rows}


def audit(base_path,prior_path,new_path,manifest_path):
    base=check(base_path,BASE_SHA,4413)
    prior=check(prior_path,PRIOR_SHA,4501)
    latest=check(new_path,NEW_SHA,4509)
    if not set(base)<=set(prior)<=set(latest):
        raise ValueError("A_FROZEN_RECORD_WAS_REMOVED")
    for older,newer in ((base,prior),(prior,latest)):
        for fid,r in older.items():
            if r!=newer[fid]:raise ValueError("IMMUTABLE_ROW_CHANGED:"+fid)
    first=set(prior)-set(base)
    late=set(latest)-set(prior)
    if len(first)!=88 or len(late)!=8:
        raise ValueError("NOT_EXACTLY_88_PLUS_8")
    if any(prior[fid]["match_date"] not in {"2026-10-30","2026-10-31","2026-11-01"}
           for fid in first):
        raise ValueError("EARLIER_88_TIME_COHORT_MISMATCH")
    if any(latest[fid]["match_date"]!="2026-11-02" for fid in late):
        raise ValueError("LATEST_EIGHT_TIME_COHORT_MISMATCH")
    evidence=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if evidence.get("schema")!=SCHEMA or evidence.get("human_review_complete") is not False or evidence.get("accepted_quad_snapshot_created") is not False:
        raise ValueError("SOURCE_MUST_NOT_CLAIM_HUMAN_APPROVAL")
    listed=evidence.get("rows")
    if not isinstance(listed,list) or len(listed)!=88:
        raise ValueError("WRONG_EVIDENCE_ROW_COUNT")
    checked=set(); by=Counter();tiers=Counter()
    for item in listed:
        fid=item["fixture_id"]
        if fid in checked or fid not in first:
            raise ValueError("DUPLICATE_OR_NOT_OLDER_88:"+fid)
        checked.add(fid)
        source=prior[fid]
        if any(item[k]!=source[k] for k in ("league","match_date","home_id","away_id")):
            raise ValueError("INCORRECT_EVIDENCE_FIXTURE_IDENTITY:"+fid)
        if item["source_score"]!=source["home_goals"]+"-"+source["away_goals"]:
            raise ValueError("EXTERNAL_SCORE_MISMATCH:"+fid)
        url=item.get("source_url")
        if not isinstance(url,str) or not url.startswith("https://"):
            raise ValueError("EXTERNAL_WEB_SCORE_URL_MISSING:"+fid)
        if item.get("source_capture")!="WEB_ROUND_RESULT_TRANSCRIPTION_NOT_MACHINE_PAGE_SNAPSHOT":
            raise ValueError("FALSE_EXTERNAL_SOURCE_AUTHENTICATION_CLAIM")
        by[item["league"]]+=1;tiers[item["source_tier"]]+=1
    if checked!=first or dict(by)!=EXPECTED_BY_LEAGUE:
        raise ValueError("88_SOURCE_REFERENCES_INCOMPLETE")
    return {"schema":"263_88_source_crosscheck_audit_v1",
            "status":"WEB_ROUND_SCORE_CORROBORATION_ONLY_HUMAN_REVIEW_PENDING",
            "frozen_baseline_unchanged":len(base),
            "prior_staged_rows_unchanged":len(prior),
            "latest_preflight_rows":len(latest),
            "older_88_source_score_agreement":len(checked),
            "newest_eight_separate_earlier_web_audit":len(late),
            "source_tiers":dict(tiers),"by_league":dict(sorted(by.items())),
            "raw_source_pages_archived_and_verified":False,
            "third_party_score_reliability_guaranteed":False,
            "human_verified_source_acceptance":False,
            "forward_predictions_unlocked":False,
            "betting_authorized":False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--baseline",required=True)
    ap.add_argument("--prior",default="data/staged_263/extended_history.csv")
    ap.add_argument("--latest",required=True)
    ap.add_argument("--evidence",default="data/staged_263/2026_10_30_11_01_previous_88_web_score_refs.json")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=audit(a.baseline,a.prior,a.latest,a.evidence)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with Path(a.out).open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True,ensure_ascii=False)
        f.write("\n")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":main()
