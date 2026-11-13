#!/usr/bin/env python3
"""2025/26 ENG3/ENG4: ONE controlled bulk cross-source score audit.

Compares the existing 178 frozen score conflicts and 22 identity-only issues
against football-data.co.uk 2526/E2.csv and E3.csv in memory. Never uploads
or republishes full external CSV, adds data to training, edits main/M4, or
modifies original score rows. A failed/blocked source stays failed: no retry.
"""
from __future__ import annotations
import csv,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path("experiments/263/league_expansion")
LEDGER=ROOT/"eng3_eng4_2025_26_200_issues_20261113.csv"
QA3=ROOT/"eng3_eng4_2025_26_score_conflicts_qa_20261113.json"
QA16=ROOT/"eng3_eng4_2025_26_16_additional_external_score_checks_20261113.json"
QA6=ROOT/"eng3_eng4_2025_26_december_6_independent_checks_20261113.json"
URLS={
 "ENG3":"https://www.football-data.co.uk/mmz4281/2526/E2.csv",
 "ENG4":"https://www.football-data.co.uk/mmz4281/2526/E3.csv",
}
ISSUE_URL="https://github.com/openfootball/england/issues/62"
EXPECTED_OLD_CONFLICTS=178
EXPECTED_PRIOR=25

def norm(v):
    v=unicodedata.normalize("NFKD",v.casefold())
    v="".join(c for c in v if not unicodedata.combining(c))
    v=re.sub(r"\bpeterboro\b","peterborough",v).replace("bristol rvs","bristol rovers")
    v=v.replace("mk dons","milton keynes dons")
    v=re.sub(r"[^a-z0-9 ]"," ",v)
    v=re.sub(r"\s+"," ",v).strip()
    v=re.sub(r"^(afc|fc)\s+","",v)
    v=re.sub(r"\s+fc$","",v)
    v=re.sub(r"\s+(united|city|town|rovers|wanderers|county|athletic|stanley|alexandra|albion)$","",v)
    return re.sub(r"\s+","",v)

def key(league,day,home,away):
    return (league,day,norm(home),norm(away))

def match_score(value):
    if not re.fullmatch(r"\d{1,2}-\d{1,2}",str(value)):raise ValueError("INVALID_FT_SCORE")
    h,a=map(int,value.split("-"))
    if h>30 or a>30:raise ValueError("IMPOSSIBLE_FT_SCORE")
    return (h,a)

def date_iso(v):
    v=v.strip()
    for fmt in ("%d/%m/%y","%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
        try:return datetime.strptime(v,fmt).date().isoformat()
        except ValueError:pass
    raise ValueError("BAD_FOOTBALL_DATA_DATE")

def load_ledger():
    with LEDGER.open(encoding="utf-8",newline="") as file:
        original=list(csv.DictReader(file))
    conflicts=[r for r in original if r["issue"]=="SCORE_CONFLICT_BLOCK_TRAINING"]
    old_only=[r for r in original if r["issue"]=="MISSING_NEW_SOURCE_IDENTITY_BLOCK_TRAINING"]
    if len(original)!=200 or len(conflicts)!=178 or len(old_only)!=22:
        raise ValueError("FROZEN_LEDGER_COUNTS_CHANGED")
    identities=set()
    for r in original:
        k=key(r["league"],r["date"],r["home"],r["away"])
        if k in identities:raise ValueError("LEDGER_DUPLICATE_IDENTITY")
        identities.add(k)
        match_score(r["prior_score"])
        if r in conflicts:match_score(r["sean_score"])
    return conflicts,old_only

def previously_confirmed():
    prev={}
    with QA3.open(encoding="utf-8") as f: qa3=json.load(f)
    for r in qa3["official_web_spot_checks"]:
        home,away=r["match"].split(" - ",1)
        k=key(r["league"],r["date"],home,away)
        prev[k]=match_score(r["verified_final"])
    with QA16.open(encoding="utf-8") as f:qa16=json.load(f)
    for r in qa16["entries"]:
        k=key(r["league"],r["date"],r["home"],r["away"])
        if k in prev:raise ValueError("PREVIOUS_DUPLICATE_16")
        prev[k]=match_score(r["independently_reported_final_score"])
    with QA6.open(encoding="utf-8") as f:qa6=json.load(f)
    for r in qa6["matches"]:
        k=key(r["league"],r["date"],r["home"],r["away"])
        if k in prev:raise ValueError("PREVIOUS_DUPLICATE_6")
        prev[k]=match_score(r["verified_external_ft_score"])
    if len(prev)!=EXPECTED_PRIOR:raise ValueError("PREVIOUS_25_NOT_VERIFIED")
    return prev

def csv_source(raw,league):
    decoded=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(decoded,newline=""))
    expected={"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}
    if not expected.issubset(reader.fieldnames or []):
        raise ValueError("FOOTBALL_DATA_HEADERS_CHANGED")
    results={};malformed=Counter();invalid=[]
    rowcount=0;name_pairs={}
    for row in reader:
        if not row.get("Date"):continue
        rowcount+=1
        if row.get("Div","").strip()!=("E2" if league=="ENG3" else "E3"):
            raise ValueError("WRONG_DIVISION_IN_RESPONSE")
        d=date_iso(row["Date"])
        if not("2025-07-01"<=d<="2026-06-30"):
            malformed["outside_season"]+=1;continue
        h=row["HomeTeam"];a=row["AwayTeam"]
        if not h or not a or norm(h)==norm(a):malformed["missing_or_same_team"]+=1;continue
        hg=row.get("FTHG","");ag=row.get("FTAG","")
        if not re.fullmatch(r"\d{1,2}(?:\.0)?",str(hg)) or not re.fullmatch(r"\d{1,2}(?:\.0)?",str(ag)):
            malformed["no_fulltime_score"]+=1;continue
        home_goals=int(float(hg));away_goals=int(float(ag))
        if home_goals>30 or away_goals>30:malformed["impossible_score"]+=1;continue
        result=row.get("FTR","")
        expected_result="H" if home_goals>away_goals else ("A" if home_goals<away_goals else "D")
        if result and result!=expected_result:raise ValueError("FTR_AND_GOAL_INCONSISTENCY")
        k=key(league,d,h,a)
        if k in results:raise ValueError("THIRD_PARTY_DUPLICATE_FT_IDENTITY")
        results[k]=(home_goals,away_goals)
        name_pairs[norm(h)]=h;name_pairs[norm(a)]=a
    return results,{"raw_with_dates":rowcount,"scored_unique":len(results),"clubs_normalized":len(name_pairs),
                     "zero_zero_games":sum(v==(0,0) for v in results.values()),
                     "invalid_rows":dict(malformed)}

def check(full_sources):
    conflicts,old_only=load_ledger()
    prev=previously_confirmed()
    conflicting_keys={key(r["league"],r["date"],r["home"],r["away"]) for r in conflicts}
    if not set(prev)<=conflicting_keys:raise ValueError("PREVIOUS_25_OUTSIDE_FROZEN_178")
    output={"created_on_utc":datetime.now(timezone.utc).isoformat(),
     "mode":"ONE_BATCH_2025_26_ENG3_ENG4_THIRD_SOURCE_SCORE_COMPARISON",
     "prior_25_individually_confirmed":len(prev),
     "original_source_conflicts":len(conflicts),
     "original_old_only_identities":len(old_only),
     "github_issue_acknowledged":ISSUE_URL,
     "external_csv_rehosted":False,"new_dataset_rows":0,"training_admissions":0,
     "production_or_SHA_modified":False,"source_results":{},"summary":{}}
    resolved=Counter();by_league={}
    new_confirmed_total=0
    for league in ("ENG3","ENG4"):
        source_raw=full_sources[league]
        source,stats=csv_source(source_raw,league)
        source_file_sha=hashlib.sha256(source_raw).hexdigest()
        group=[r for r in conflicts if r["league"]==league]
        compare=Counter();samples=[];matched_before=0;new_matches=0
        for r in group:
            k=key(r["league"],r["date"],r["home"],r["away"])
            actual=source.get(k)
            if actual is None:
                compare["identity_not_matched"]+=1
                if len(samples)<18:samples.append({"date":r["date"],"home":r["home"],"away":r["away"],"kind":"NO_EXACT_SOURCE_ID"})
                continue
            original=match_score(r["prior_score"])
            alternate=match_score(r["sean_score"])
            if k in prev and prev[k]!=alternate:raise ValueError("PREVIOUS_OFFICIAL_WITNESS_DISAGREES_WITH_ALT")
            if actual==alternate:
                compare["alternate_confirmed_by_3rd_score_source"]+=1
                if k in prev:matched_before+=1
                else:new_matches+=1
            elif actual==original:
                compare["original_supported_by_3rd_score_source"]+=1
                if len(samples)<18:samples.append({"date":r["date"],"home":r["home"],"away":r["away"],"kind":"OLD_SCORE_SUPPORTED"})
            else:
                compare["neither_score_matches_3rd_source"]+=1
                if len(samples)<18:samples.append({"date":r["date"],"home":r["home"],"away":r["away"],"kind":"THIRD_SCORE"})
        identity_group=[r for r in old_only if r["league"]==league]
        old_keys_found=0;old_score_same=0;old_score_diff=0
        for r in identity_group:
            k=key(league,r["date"],r["home"],r["away"])
            third=source.get(k)
            if third is not None:
                old_keys_found+=1
                if third==match_score(r["prior_score"]):old_score_same+=1
                else:old_score_diff+=1
        by_league[league]={
          "source_url":URLS[league], "source_sha256":source_file_sha,
          "source_row_diagnostics":stats,"conflicts_in_ledger":len(group),
          "score_check_counts":dict(compare),
          "prior_editorial_confirmed_matched_in_batch":matched_before,
          "new_alternate_match_scores_from_third_compilation":new_matches,
          "old_only_identity_issues":len(identity_group),
          "old_only_found_in_third_source":old_keys_found,
          "old_only_equal_old_score":old_score_same,
          "old_only_differ_old_score":old_score_diff,
          "exceptions":samples
        }
        resolved.update(compare);new_confirmed_total+=new_matches
    by_counts=sum(sum(x["score_check_counts"].values()) for x in by_league.values())
    if by_counts!=178:raise ValueError("NOT_ALL_178_EXAMINED")
    output["source_results"]=by_league
    output["summary"]={
        **dict(resolved),
        "newly_third_source_corrobated_beyond_prior_25":new_confirmed_total,
        "remaining_without_third_source_alternate_confirmation":178-len(prev)-new_confirmed_total,
        "third_party_license_and_republication_review":"PENDING",
        "source_status":"SCORE_PROVENANCE_ONLY_NO_TRAINING"
    }
    return output

def get(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; personal-results-accuracy-check/1.0)",
                            "Accept":"text/csv,application/csv;q=0.8"})
    with urlopen(req,timeout=20) as resp:
        blob=resp.read(3_000_001)
        if len(blob)>3_000_000:raise ValueError("REMOTE_BODY_TOO_LARGE")
    return blob

def selftest():
    assert norm("Peterboro") == norm("Peterborough United")
    assert norm("MK Dons") == norm("Milton Keynes Dons")
    assert norm("Bristol Rvs") == norm("Bristol Rovers")
    assert norm("AFC Wimbledon") == norm("Wimbledon")
    assert norm("Crewe Alexandra") == norm("Crewe")
    assert norm("Wycombe Wanderers") == norm("Wycombe")
    assert len(load_ledger()[0])==178 and len(previously_confirmed())==25
    ex=b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE2,08/11/25,Bolton,Port Vale,4,0,H\nE2,15/11/25,Luton,Rotherham,0,0,D\n"
    m,info=csv_source(ex,"ENG3")
    assert m[key("ENG3","2025-11-08","Bolton Wanderers","Port Vale")]==(4,0)
    assert info["zero_zero_games"]==1
    print("PASS synthetic: source alias / 0-0 / three-way score QC / 178+22 issue ledger and prior 25")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--live",action="store_true")
    opt=p.parse_args()
    if opt.self_test:selftest()
    if opt.live:
        report={"status":"NOT_COMPLETED","scope":"2025_26_ENG3_ENG4","trainable_new_rows":0,"raw_CSV_copied":False}
        try:
            streams={k:get(URLS[k]) for k in ("ENG3","ENG4")}
            report.update(check(streams))
            report["status"]="THIRD_SOURCE_COMPARISON_COMPLETE"
        except Exception as ex:
            report["status"]="FAIL_CLOSED_THIRD_PARTY_ACCESS_OR_QA"
            report["blocked_error_class"]=type(ex).__name__
            report["blocked_http_status"]=getattr(ex,"code",None)
            report["error_reason"]=str(ex)[:140] if isinstance(ex,ValueError) else "source unavailable"
        print("ENG_SCORE_BATCH_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("ENG_SCORE_BATCH_END")
