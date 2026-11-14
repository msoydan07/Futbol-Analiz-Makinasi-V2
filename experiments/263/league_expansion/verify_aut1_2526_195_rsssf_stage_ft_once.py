#!/usr/bin/env python3
"""NEW 2025/26 Austria Bundesliga source-result QA: 195 independently listed
match dates, home/away, fulltime scores, and stages (132 + 30 + 30 + 3).

Original frozen CC0 scores (67 + 128) are read-only; RSSSF HTML is queried once,
parsed IN MEMORY, not copied to GitHub. No training, no production M4 edits.
Unlabeled initial 67 stage names are adjudicated *against* the independent
regular-stage section (not inferred solely by calendar).
"""
from __future__ import annotations
from collections import Counter
from datetime import date,datetime,timezone
import hashlib,json,re,sys,unicodedata
from urllib.request import Request,urlopen

from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,read_csv
from verify_che1_2526_rsssf_fullseason_once import to_lines

RSSSF="https://www.rsssf.org/tableso/oost2026.html"
ALT_RSSSF="https://rsssf.github.io/tables/oost2026.html"
PRIMARY=["training_2025_26_cc0_scored_QUARANTINE.csv",
         "score_shape_recovery_295_2526_QUARANTINE_20261113.csv"]
SECTIONS={"regular":132,"championship":30,"relegation":30,"conference_playoff":3}
ALIASES={
 "LASK":"LASK","Sturm":"Sturm Graz","Wolfsberg":"Wolfsberger AC",
 "Wattens":"WSG Tirol","Hartberg":"TSV Hartberg","Ried":"SV Ried",
 "Salzburg":"RB Salzburg","GAK":"Grazer AK","Rapid":"Rapid Wien",
 "BW Linz":"FC Blau Weiß Linz","Austria W":"Austria Wien",
 "Altach":"SCR Altach"
}
MONTHS={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
        "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
RESULT=re.compile(r"^\s*([^0-9\[\]\n]+?)\s+(\d{1,2})-(\d{1,2})\s+([^0-9\[\]\n]+?)\s*$")
DATE=re.compile(r"\[\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s*\]",re.I)

def canonical(s):
    return re.sub(r"[^a-z0-9]","",
        "".join(c for c in unicodedata.normalize("NFKD",s.casefold())
                if not unicodedata.combining(c)))

lookup={canonical(s):canonical(v) for s,v in ALIASES.items()}
lookup.update({canonical(v):canonical(v) for v in ALIASES.values()})

def ft(v1,v2):
    if not (re.fullmatch(r"\d{1,2}",str(v1)) and re.fullmatch(r"\d{1,2}",str(v2))):
        raise ValueError("INVALID_SOURCE_FT")
    a,b=int(v1),int(v2)
    if a>30 or b>30:raise ValueError("SCORE_OUT_OF_RANGE")
    return a,b

def get_data():
    problems=[]
    for url in (RSSSF,ALT_RSSSF):
        try:
            req=Request(url,headers={
                "User-Agent":"Mozilla/5.0 (compatible; historical-match-score-audit/1.0)",
                "Accept":"text/html"})
            with urlopen(req,timeout=25) as rsp:
                blob=rsp.read(500_001)
                if len(blob)>500_000:raise ValueError("RSSSF_PAGE_TOO_LARGE")
            if b"Austria 2025/26" not in blob:
                raise ValueError("WRONG_AUSTRIAN_ARCHIVE")
            return blob,url
        except Exception as e:
            problems.append(type(e).__name__)
    raise ValueError("RSSSF_HOSTS_UNAVAILABLE:"+",".join(problems))

def line_index(lines,pattern,start=0):
    return next((i for i in range(start,len(lines)) if re.fullmatch(pattern,lines[i].strip(),re.I)),None)

def parse_block(lines,section):
    out={};without_date=[];unknown=[];duplicate=[];day=None
    for raw in lines:
        match=DATE.search(raw)
        if match:
            month=MONTHS[match.group(1).capitalize()]
            y=2025 if month>=7 else 2026
            day=date(y,month,int(match.group(2))).isoformat()
        m=RESULT.fullmatch(raw)
        if not m:continue
        h=lookup.get(canonical(m.group(1)))
        a=lookup.get(canonical(m.group(4)))
        if h is None or a is None:
            if h or a:unknown.append((m.group(1),m.group(4)))
            continue
        if h==a:raise ValueError("RSSSF_SAME_TEAM")
        if not day:without_date.append((m.group(1),m.group(4)));continue
        k=(day,h,a)
        score=ft(m.group(2),m.group(3))
        if k in out:
            duplicate.append(k)
            if out[k]!=score:raise ValueError("RSSSF_CONFLICTING_DUPLICATE")
        out[k]=score
    return out,{"section":section,"matched":len(out),
                "unknown_one_mapped":unknown[:6],
                "no_date":len(without_date),"dup":len(duplicate)}

def parse_rsssf(raw):
    html=raw.decode("utf-8","replace")
    lines=to_lines(html)
    start=line_index(lines,r"Round\s+1\b(?:\s+\[.*\])?",0)
    play=line_index(lines,r"Playoff Stage",start or 0)
    if start is None or play is None or play<=start:raise ValueError("NO_REGULAR_SECTION")
    champ=line_index(lines,r"Round\s+23\b(?:\s+\[.*\])?",play)
    conf=line_index(lines,r"Conference League Playoff",champ or 0)
    releg=line_index(lines,r"Relegation Playoff",conf or 0)
    relstart=line_index(lines,r"Round\s+23\b(?:\s+\[.*\])?",releg or 0)
    finish=line_index(lines,r"Final Table:?",relstart or 0)
    if None in (champ,conf,releg,relstart,finish):
        raise ValueError("RSSSF_STAGE_SECTION_BOUNDARIES_NOT_FOUND")
    if not (start<play<champ<conf<releg<relstart<finish):
        raise ValueError("STAGE_ORDERING_ERROR")
    spans={
      "regular":(start,play),
      "championship":(champ,conf),
      "conference_playoff":(conf,releg),
      "relegation":(relstart,finish)
    }
    data={};diagnostics={};all_keys=set()
    for stage,(lo,hi) in spans.items():
        x,diag=parse_block(lines[lo:hi],stage)
        if len(x)!=SECTIONS[stage]:
            diag["stage_expected"]=SECTIONS[stage]
        if all_keys & set(x):raise ValueError("CROSS_STAGE_EXACT_MATCH_DUPLICATE")
        all_keys.update(x)
        data.update({key:(score,stage) for key,score in x.items()})
        diagnostics[stage]=diag
    return data,diagnostics

def primary_rows():
    found={};sources=Counter();stage_counts=Counter()
    for filename in PRIMARY:
        expected_sha,expected_count,kind=EXPECTED[filename]
        all_rows,sha=read_csv(filename)
        if sha!=expected_sha or len(all_rows)!=expected_count:
            raise ValueError("SOURCE_BLOB_PIN_DRIFT")
        for row in all_rows:
            if row["league"]!="AUT1" or row["season"]!="2025-26":continue
            d=date.fromisoformat(row["date"])
            if not date(2025,7,1)<=d<=date(2026,6,30):
                raise ValueError("SOURCE_DATE_OUTSIDE_2025_26")
            h=lookup.get(canonical(row["home"]))
            a=lookup.get(canonical(row["away"]))
            if not h or not a or h==a:raise ValueError("PRIMARY_TEAM_ALIAS_FAIL")
            k=(d.isoformat(),h,a)
            if k in found:raise ValueError("DUPLICATE_PRIMARY_AUSTRIA_MATCH")
            stage_raw=row.get("round_stage","")
            if "Championship Round" in stage_raw:stage="championship"
            elif "Relegation Round" in stage_raw:stage="relegation"
            elif "Conference League Play-offs" in stage_raw:stage="conference_playoff"
            elif "Regular Season" in stage_raw:stage="regular"
            elif not stage_raw and filename==PRIMARY[0]:stage="undeclared"
            else:stage="unknown"
            found[k]=(ft(row["ft_home"],row["ft_away"]),stage,filename)
            sources[filename]+=1;stage_counts[stage]+=1
    if len(found)!=195 or sources[PRIMARY[0]]!=67 or sources[PRIMARY[1]]!=128:
        raise ValueError("PRIMARY_COUNTS_CHANGED")
    if stage_counts!=Counter({"undeclared":67,"regular":65,"championship":30,
                              "relegation":30,"conference_playoff":3}):
        raise ValueError("PRIMARY_STAGE_COUNTS_CHANGED")
    return found,dict(sources)

def audit():
    primary,sources=primary_rows()
    blob,source_url=get_data()
    independ,sections=parse_rsssf(blob)
    stage_match=Counter();score_match=Counter()
    not_in_rsssf=[];different_score=[];different_stage=[];unlabeled_confirmed=0
    for k,(score,stage,source) in primary.items():
        entry=independ.get(k)
        if entry is None:
            if len(not_in_rsssf)<12:not_in_rsssf.append(
                {"date":k[0],"home":k[1],"away":k[2]})
            continue
        other_ft,other_stage=entry
        if other_ft!=score:
            if len(different_score)<12:different_score.append(
                {"date":k[0],"home":k[1],"away":k[2],
                 "source_ft":list(score),"independent_ft":list(other_ft)})
        else:score_match[stage]+=1
        if stage=="undeclared":
            if other_stage=="regular":unlabeled_confirmed+=1
            else:different_stage.append({"date":k[0],"home":k[1],"away":k[2],
                                         "source":"no_stage","rsssf":other_stage})
        elif stage!=other_stage:
            different_stage.append({"date":k[0],"home":k[1],"away":k[2],
                                    "source_stage":stage,"rsssf_stage":other_stage})
        else:stage_match[stage]+=1
    missing_from_primary=set(independ)-set(primary)
    complete=(len(independ)==195 and len(primary)==195
              and not not_in_rsssf and not different_score and
              not different_stage and not missing_from_primary
              and unlabeled_confirmed==67
              and all(sections[x]["matched"]==SECTIONS[x] for x in SECTIONS))
    return {
      "run_utc":datetime.now(timezone.utc).isoformat(),
      "league":"AUT1","season":"2025-26",
      "status":"195_OF_195_INDEPENDENT_DATE_CLUB_FT_STAGE_PASS" if complete
                else "FAIL_CLOSED_INDEPENDENT_MATCH_QA_NOT_COMPLETE",
      "score_source":"Original 195 CC0 OpenFootball published scored research candidates",
      "independent_source":source_url,
      "independent_html_sha256":hashlib.sha256(blob).hexdigest(),
      "primary_rows":len(primary),"primary_source_distribution":sources,
      "rsssf_results":len(independ),
      "section_counts":sections,
      "fulltime_score_equal_by_prior_stage":dict(score_match),
      "unlabeled_early_67_explicitly_confirmed_regular_by_independent_source":unlabeled_confirmed,
      "score_conflict_examples":different_score,
      "not_in_rsssf_examples":not_in_rsssf,
      "different_stage_examples":different_stage[:12],
      "only_in_rsssf_number":len(missing_from_primary),
      "regular_22_rounds":132 if complete else None,
      "championship_10_rounds":30 if complete else None,
      "relegation_10_rounds":30 if complete else None,
      "conference_league_playoffs_not_normal_league":3 if complete else None,
      "publisher_CC0_rights_claim":"Source repository CC0; verify upstream rights separately",
      "RSSSF_license_to_rehost_match_database":"NOT_ESTABLISHED; no raw content retained",
      "new_training_admissions":0,"research_quarantine_rows_added":0,
      "source_primary_CSV_mutated":False,"main_M4_SHA_modified":False
    }

def selftest():
    small=[
      "Round 1","[Aug 1]","LASK             0-2 Sturm",
      "[Aug 2]","Wolfsberg        0-2 Altach",
      "[Aug 3]","Rapid            1-0 BW Linz"]
    r,diag=parse_block(small,"regular")
    assert len(r)==3
    assert r[("2025-08-01",canonical("LASK"),canonical("Sturm Graz"))]==(0,2)
    assert r[("2025-08-03",canonical("Rapid Wien"),canonical("FC Blau Weiß Linz"))]==(1,0)
    assert len(primary_rows()[0])==195
    print("PASS 195 pinned research rows, RSSSF team aliases, 2025-08 date, regular stage score parsing")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--live",action="store_true")
    arg=parser.parse_args()
    if arg.self_test:selftest()
    if arg.live:
        try:
            result=audit()
        except Exception as error:
            result={"status":"FAIL_CLOSED_INDEPENDENT_SOURCE_OR_PARSER",
                    "error_class":type(error).__name__,
                    "error_details":str(error)[:170] if isinstance(error,ValueError) else "external provider unavailable",
                    "training_rows_added":0,"original_rows_unchanged":True}
        print("AUT195_AUDIT_START")
        print(json.dumps(result,indent=2,ensure_ascii=False))
        print("AUT195_AUDIT_END")
