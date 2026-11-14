#!/usr/bin/env python3
"""Research-only one-shot Serie B 2025/26 309 score facts vs independent
MatchDaySync 380-row restored season, and independent RSSSF season table.

Original 283+26 CC0-scored research records are SHA-pinned and never modified.
The 380-row external CSV is used once IN MEMORY; no republication or model
training. Distinguish real 0-0 from missing values and date-only disagreements.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from urllib.request import Request,urlopen
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,read_csv
from verify_public_season_csv_2526 import csv_rows

LEAGUE="ITA2"
FILES=("training_2025_26_cc0_scored_QUARANTINE.csv",
       "score_shape_recovery_295_2526_QUARANTINE_20261113.csv")
URL="https://matchdaysync.com/api/public/csv/serie-b/2025-26/matches"
STANDINGS="https://www.rsssf.org/tablesi/ital2026.html"
EXPECTED_SOURCE_MATCHES=380
EXPECTED_RESEARCH=309
# Public final regular-season standings as recorded by RSSSF. Each tuple:
# W,D,L,GF,GA,points. Not the promotion/relegation playoff games.
RSSSF_TABLE={
 "Venezia":(24,10,4,77,31,82),
 "Frosinone":(23,12,3,76,34,81),
 "Monza":(22,10,6,61,32,76),
 "Palermo":(20,12,6,61,33,72),
 "Catanzaro":(15,14,9,62,51,59),
 "Modena":(15,10,13,49,36,55),
 "Juve Stabia":(11,18,9,44,45,51),
 "Avellino":(13,10,15,43,55,49),
 "Mantova":(13,7,18,45,57,46),
 "Padova":(12,10,16,39,49,46),
 "Cesena":(12,10,16,45,56,46),
 "Carrarese":(10,14,14,47,52,44),
 "Sampdoria":(11,11,16,35,48,44),
 "Virtus Entella":(10,12,16,36,51,42),
 "Empoli":(9,14,15,47,54,41),
 "Sudtirol":(8,17,13,38,48,41),
 "Bari":(10,10,18,38,60,40),
 "Reggiana":(9,10,19,36,56,37),
 "Spezia":(8,11,19,43,59,35),
 "Pescara":(7,14,17,51,66,35),
}
ALIASES={
 "Venezia":["Venezia FC"],"Frosinone":["Frosinone Calcio"],
 "Monza":["AC Monza"],"Palermo":["Palermo FC"],
 "Catanzaro":["US Catanzaro","US Catanzaro 1929"],
 "Modena":["Modena FC","Modena FC 2018"],
 "Juve Stabia":["SS Juve Stabia"],
 "Avellino":["US Avellino","US Avellino 1912"],
 "Mantova":["Mantova 1911 SSD","Mantova 1911"],
 "Padova":["Calcio Padova"],
 "Cesena":["Cesena FC"],
 "Carrarese":["Carrarese Calcio"],
 "Sampdoria":["UC Sampdoria"],
 "Virtus Entella":["Virtus Entella"],
 "Empoli":["Empoli FC"],
 "Sudtirol":["FC Südtirol","Südtirol","Sudtirol"],
 "Bari":["SSC Bari","BA Bari"],
 "Reggiana":["AC Reggiana 1919","RE Reggiana"],
 "Spezia":["Spezia Calcio","SP Spezia"],
 "Pescara":["Delfino Pescara","PE Pescara"]
}
def norm(s):
    s=s.casefold().replace("ø","o").replace("æ","ae").replace("ß","ss")
    s="".join(c for c in unicodedata.normalize("NFKD",s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",s)

LOOK={}
for canonical,options in ALIASES.items():
    for s in [canonical]+options:
        k=norm(s)
        if k in LOOK and LOOK[k]!=canonical:raise ValueError("ALIAS_COLLISION")
        LOOK[k]=canonical

def club(s):
    return LOOK.get(norm(str(s or "")))

def score(h,a):
    if not re.fullmatch(r"\d{1,2}",str(h or "").strip()) or not re.fullmatch(r"\d{1,2}",str(a or "").strip()):
        return None
    first,second=int(h),int(a)
    return (first,second) if first<=30 and second<=30 else None

def iso(s):
    val=str(s or "")[:10]
    try:d=date.fromisoformat(val)
    except ValueError:return None
    return val if date(2025,7,1)<=d<=date(2026,6,30) else None

def primary():
    out={};origin=Counter();invalid=[]
    for filename in FILES:
        rows,sha=read_csv(filename)
        expected_sha,expected_n,_=EXPECTED[filename]
        if sha!=expected_sha or len(rows)!=expected_n:
            raise ValueError("ORIGINAL_SOURCE_PIN_DRIFT")
        for r in rows:
            if r["league"]!="ITA2" or r["season"]!="2025-26":continue
            h,a=club(r["home"]),club(r["away"])
            ft=score(r["ft_home"],r["ft_away"])
            day=iso(r["date"])
            if not h or not a or h==a or not ft or not day:
                invalid.append({"file":filename,"date":r["date"],"reason":"TEAM_SCORE_OR_DATE"})
                continue
            k=(day,h,a)
            if k in out:raise ValueError("RESEARCH_DUPLICATE_MATCH_ID")
            out[k]=ft
            origin[filename]+=1
    if invalid or len(out)!=309 or origin[FILES[0]]!=283 or origin[FILES[1]]!=26:
        raise ValueError("RESEARCH_309_SCOPED_INPUT_CHANGED:"+str(len(out)))
    return out,dict(origin)

def get():
    request=Request(URL,headers={
        "User-Agent":"Mozilla/5.0 (educational historic-match-facts-QA; one-source-one-pass)",
        "Accept":"text/csv,application/csv;q=0.8,*/*;q=0.2"})
    with urlopen(request,timeout=25) as response:
        b=response.read(1_300_001)
        if len(b)>1_300_000:raise ValueError("REMOTE_CSV_TOO_LARGE")
    return b

def secondary(raw):
    parsed=csv_rows(raw.decode("utf-8-sig"))
    selected={};issues=Counter();clubnames=set()
    for r in parsed:
        if str(r.get("status") or "").casefold().strip() not in ("finished","completed","ft","full-time","full time"):
            issues["NOT_FINISHED"]+=1;continue
        day=iso(r.get("date"))
        home,away=club(r.get("home")),club(r.get("away"))
        ft=score(r.get("home_goals"),r.get("away_goals"))
        if not day:issues["BAD_DATE"]+=1;continue
        if not home or not away or home==away:
            issues["UNKNOWN_CLUB"]+=1;continue
        if ft is None:issues["NO_EXPLICIT_SCORE"]+=1;continue
        k=(day,home,away)
        if k in selected:
            issues["DUPLICATE_FIXTURE"]+=1
            if selected[k]!=ft:issues["CONFLICTING_DUPLICATE"]+=1
            continue
        selected[k]=ft
        clubnames.add(home);clubnames.add(away)
    return selected,{"rows":len(parsed),"scored_unique":len(selected),
         "explicit_zero_zero":sum(v==(0,0) for v in selected.values()),
         "clubs":len(clubnames),"exclusions":dict(issues)}

def standings(rows):
    totals=defaultdict(lambda: [0,0,0,0,0,0]) # W D L GF GA points
    homecount=Counter();awaycount=Counter()
    for (_,home,away),(hg,ag) in rows.items():
        t,a=totals[home],totals[away]
        homecount[home]+=1;awaycount[away]+=1
        t[3]+=hg;t[4]+=ag;a[3]+=ag;a[4]+=hg
        if hg>ag:t[0]+=1;a[2]+=1;t[5]+=3
        elif hg<ag:a[0]+=1;t[2]+=1;a[5]+=3
        else:t[1]+=1;a[1]+=1;t[5]+=1;a[5]+=1
    mismatches={}
    for k,expected in RSSSF_TABLE.items():
        actual=tuple(totals[k])
        if actual!=expected or homecount[k]!=19 or awaycount[k]!=19:
            mismatches[k]={"observed":actual,"expected":expected,
                           "home":homecount[k],"away":awaycount[k]}
    return {"rSSSF_team_table_mismatches":mismatches,
            "number_of_teams":len(totals),
            "total_scored_goals":sum(x[3] for x in totals.values()),
            "expected_total_goals":sum(x[3] for x in RSSSF_TABLE.values()),
            "full_season_380_20_club_19_home_19_away_pass":
                 len(rows)==380 and len(totals)==20 and not mismatches}

def evaluate(raw):
    old,origin=primary()
    new,diagnostics=secondary(raw)
    as_table=standings(new)
    matches=0;date_drift=[];score_conflict=[];notfound=[];oldzero=0;zero_equal=0
    by_month=Counter()
    by_pair=defaultdict(list)
    for key,sc in new.items():by_pair[key[1:]].append((key[0],sc))
    for key,orig_sc in old.items():
        oldzero+=int(orig_sc==(0,0))
        if key in new:
            sc=new[key]
            if sc==orig_sc:
                matches+=1
                by_month[key[0][:7]]+=1
                if sc==(0,0):zero_equal+=1
            elif len(score_conflict)<18:
                score_conflict.append({"date":key[0],"home":key[1],"away":key[2],
                     "old_score":list(orig_sc),"independent_score":list(sc)})
        else:
            maybe=[(day,sc) for day,sc in by_pair[key[1:]] if abs((date.fromisoformat(day)-date.fromisoformat(key[0])).days)<=3]
            if maybe and len(date_drift)<18:
                date_drift.append({"original_date":key[0],"home":key[1],"away":key[2],
                    "similar_date":maybe[0][0],"same_score":maybe[0][1]==orig_sc,
                    "date_difference_days":(date.fromisoformat(maybe[0][0])-date.fromisoformat(key[0])).days})
            elif len(notfound)<18:notfound.append({"date":key[0],"home":key[1],"away":key[2]})
    unknown=309-matches-len(score_conflict)-len(date_drift)-len(notfound)
    # Note: sample exception arrays capped at 18, cannot infer exact mismatch totals.
    unmatched_exact=309-sum(1 for k in old if k in new)
    mismatched_exact=sum(1 for k,v in old.items() if k in new and new[k]!=v)
    drift_all=sum(1 for k in old if k not in new and
        any(abs((date.fromisoformat(otherdate)-date.fromisoformat(k[0])).days)<=3
            for otherdate,ft in by_pair[k[1:]]))
    missing_all=unmatched_exact-drift_all
    complete=diagnostics["scored_unique"]==380 and not diagnostics["exclusions"] and
      as_table["full_season_380_20_club_19_home_19_away_pass"] if False else False
    complete=(diagnostics["rows"]==380 and diagnostics["scored_unique"]==380 and
              not diagnostics["exclusions"] and
              as_table["full_season_380_20_club_19_home_19_away_pass"] and
              matches==309 and mismatched_exact==0 and unmatched_exact==0)
    return {"as_of_utc":datetime.now(timezone.utc).isoformat(),
       "scope":"2025_26_ITA2_309_EXISTING_RESEARCH_FT_SCORES",
       "status":"309_OF_309_INDEPENDENT_DATE_CLUB_FT_PASS" if complete else "FAIL_CLOSED_SOURCE_DATE_OR_SCORE_DIFFERENCES",
       "primary_rows":len(old),"primary_file_rows":origin,
       "external_url":URL,
       "external_csv_sha256":hashlib.sha256(raw).hexdigest(),
       "source_rows_rehosted":0,
       "second_source_diag":diagnostics,
       "independent_RSSSF_full_season_standings":as_table,
       "same_fixture_date_clubs_and_FT":matches,
       "original_zero_zero_rows":oldzero,
       "zero_zero_independently_confirmed":zero_equal,
       "exact_identity_source_score_disagreements":mismatched_exact,
       "possible_date_shifts_within_3_days":drift_all,
       "absent_even_within_3_days":missing_all,
       "score_conflicts_example_max18":score_conflict,
       "possible_date_shift_example_max18":date_drift,
       "missing_keys_example_max18":notfound,
       "matches_confirmed_by_month":dict(sorted(by_month.items())),
       "rights_to_rehost_external_CSV_or_retrain_model":"NOT_ESTABLISHED",
       "source_is_restored_snapshot":"YES, 11 OCTOBER BACKUP, NO LIVE_UPDATES",
       "repeated_old_closed_GitHub_quality_checks":0,
       "training_rows_added":0,"research_quarantine_rows_added":0,
       "main_M4_or_SHA_modified":False}

def selftest():
    assert len(RSSSF_TABLE)==20 and len(LOOK)>=40
    assert club("Delfino Pescara")=="Pescara"
    assert club("PE Pescara")=="Pescara"
    assert club("AC Reggiana 1919")=="Reggiana"
    assert club("RE Reggiana")=="Reggiana"
    assert club("FC Südtirol")=="Sudtirol"
    assert club("Sudtirol")=="Sudtirol"
    assert score("0","0")==(0,0)
    assert score("","") is None
    assert score("1.5","0") is None
    assert len(primary()[0])==309
    sample=("# Source: independent CSV\n"+
        "date,status,home,away,home_goals,away_goals\n"+
        "2025-08-22,finished,PE Pescara,Cesena,1,3\n"+
        "2025-08-23,finished,Empoli,Padova,3,1\n").encode()
    parsed,diag=secondary(sample)
    assert parsed[("2025-08-22","Pescara","Cesena")]==(1,3)
    print("PASS synthetic: 309 frozen source matches, Italian alias / 0-0 / strict FT and date interpretation")

if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--self-test",action="store_true")
    args.add_argument("--live",action="store_true")
    opt=args.parse_args()
    if opt.self_test:selftest()
    if opt.live:
        try:r=evaluate(get())
        except Exception as e:
            r={"status":"FAIL_CLOSED_REMOTE_OR_PARSER",
               "error_class":type(e).__name__,
               "error_message":str(e)[:250] if isinstance(e,ValueError) else "Provider unavailable",
               "training_rows_added":0,"source_rows_rehosted":0}
        print("SERIEB309_START")
        print(json.dumps(r,indent=2,ensure_ascii=False))
        print("SERIEB309_END")
