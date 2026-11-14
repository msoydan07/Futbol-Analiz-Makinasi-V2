#!/usr/bin/env python3
"""Research-only ONE BATCH: 2025/26 GER2 (99), FRA2 (116), ESP2 (131).

Second-source historical FT facts via football-data.co.uk D2/F2/SP2.csv.
Only in-memory score/fixture comparisons. Original 346 immutable CC0 rows,
upstream CSVs and existing 2396 quarantine records are NEVER republished,
overwritten, trained on, or copied into M4. Successful score QA does not grant
model-training rights or establish pre-kickoff feature-vintage provenance.

This compares a NEW 346-row group, not old completed 178/22/472/420/50/195/309.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from urllib.request import Request,urlopen
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,read_csv

SOURCE="https://www.football-data.co.uk/mmz4281/2526/"
LEAGUES={
 "GER2":{"division":"D2","expected":99,"zero":5,"clubs":18,
 "aliases":{
 "1. FC Kaiserslautern":["Kaiserslautern","Kaiserslautern FC"],
 "1. FC Magdeburg":["Magdeburg"],
 "1. FC Nürnberg":["Nurnberg","Nuremberg","Nuernberg"],
 "Arminia Bielefeld":["Bielefeld","Arminia Bielefeld"],
 "Dynamo Dresden":["Dresden"],
 "Eintracht Braunschweig":["Braunschweig"],
 "FC Schalke 04":["Schalke","Schalke 04"],
 "Fortuna Düsseldorf":["Dusseldorf","Fortuna Dusseldorf","Düsseldorf"],
 "Hannover 96":["Hannover"],
 "Hertha BSC":["Hertha","Hertha Berlin"],
 "Holstein Kiel":["Holstein Kiel","Kiel"],
 "Karlsruher SC":["Karlsruhe","Karlsruher"],
 "Preußen Münster":["Preussen Munster","Munster","Preussen Münster"],
 "SC Paderborn 07":["Paderborn","Paderborn 07"],
 "SV 07 Elversberg":["Elversberg"],
 "SV Darmstadt 98":["Darmstadt","Darmstadt 98"],
 "SpVgg Greuther Fürth":["Greuther Furth","Greuther Fürth","Furth"],
 "VfL Bochum":["Bochum"],
 }},
 "FRA2":{"division":"F2","expected":116,"zero":9,"clubs":18,
 "aliases":{
 "AS Nancy Lorraine":["Nancy","Nancy Lorraine"],
 "AS Saint-Étienne":["St Etienne","St. Etienne","Saint Etienne"],
 "Amiens SC":["Amiens"],
 "Clermont Foot 63":["Clermont","Clermont Foot"],
 "EA Guingamp":["Guingamp"],
 "ESTAC Troyes":["Troyes"],
 "FC Annecy":["Annecy"],
 "Grenoble Foot 38":["Grenoble","Grenoble Foot"],
 "Le Mans FC":["Le Mans","Le Mans FC"],
 "Montpellier HSC":["Montpellier"],
 "Pau FC":["Pau"],
 "Red Star FC":["Red Star"],
 "Rodez AF":["Rodez"],
 "SC Bastia":["Bastia"],
 "Stade Lavallois":["Laval"],
 "Stade de Reims":["Reims"],
 "US Boulogne":["Boulogne","Boulogne-sur-Mer"],
 "USL Dunkerque":["Dunkerque"],
 }},
 "ESP2":{"division":"SP2","expected":131,"zero":16,"clubs":22,
 "aliases":{
 "AD Ceuta FC":["Ceuta","AD Ceuta"],
 "Albacete":["Albacete"],
 "Burgos CF":["Burgos"],
 "CD Castellón":["Castellon","Castellón"],
 "CD Leganés":["Leganes","Leganés"],
 "CD Mirandés":["Mirandes"],
 "Cultural Leonesa":["Leonesa","Cultural Leonesa"],
 "Cádiz CF":["Cadiz"],
 "Córdoba CF":["Cordoba"],
 "Deportivo La Coruña":["La Coruna","Dep. La Coruna","Dep La Coruna","Dep. La Coruña","Deportivo","La Coruña"],
 "FC Andorra":["Andorra"],
 "Granada CF":["Granada"],
 "Málaga CF":["Malaga"],
 "Racing Santander":["Santander","Racing Santander"],
 "Real Sociedad B":["Sociedad B","Real Sociedad B"],
 "Real Valladolid":["Valladolid"],
 "Real Zaragoza":["Zaragoza"],
 "SD Eibar":["Eibar"],
 "SD Huesca":["Huesca"],
 "Sporting Gijón":["Sp Gijon","Sp. Gijon","Gijon","Sporting Gijon"],
 "UD Almería":["Almeria"],
 "UD Las Palmas":["Las Palmas"],
 }}
}
INPUT_FILES=[
 "training_2025_26_cc0_scored_QUARANTINE.csv",
 "score_shape_recovery_295_2526_QUARANTINE_20261113.csv",
]
REFERENCE_SEASON_START=date(2025,7,1)
REFERENCE_SEASON_END=date(2026,6,30)
# Only retrieve/parse first 2025-26 season outcomes through November 20 for
# these frozen records, preventing season-playoff complications or future leaks.
SECOND_SOURCE_COMPARE_CUTOFF=date(2025,11,20)

def norm(v):
    v=unicodedata.normalize("NFKD",str(v or "").casefold())
    v="".join(c for c in v if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",v)

def lookups(league):
    data=LEAGUES[league]["aliases"]
    lookup={}
    for original,variants in data.items():
        for s in (original,*variants):
            normalized=norm(s)
            if normalized in lookup and lookup[normalized]!=original:
                raise ValueError("ALIAS_COLLISION:"+s)
            lookup[normalized]=original
    if len(data)!=LEAGUES[league]["clubs"]:
        raise ValueError("ALIAS_CLUB_COUNT_CHANGED")
    return lookup

def fulltime(h,a):
    if not re.fullmatch(r"\d{1,2}",str(h or "")) or not re.fullmatch(r"\d{1,2}",str(a or "")):
        return None
    x,y=int(h),int(a)
    if x>30 or y>30:return None
    return x,y

def scored_date(s):
    text=str(s or "").strip()
    for fmt in ("%d/%m/%y","%d/%m/%Y","%d-%m-%y","%d-%m-%Y","%Y-%m-%d"):
        try:return datetime.strptime(text,fmt).date()
        except ValueError:pass
    return None

def primary():
    result={lg:{} for lg in LEAGUES}
    sources={lg:Counter() for lg in LEAGUES}
    for filename in INPUT_FILES:
        rows,git_sha=read_csv(filename)
        expected_sha,expected_rows,_=EXPECTED[filename]
        if git_sha!=expected_sha or len(rows)!=expected_rows:
            raise ValueError("PINNED_ORIGINAL_SOURCE_MISMATCH:"+filename)
        for r in rows:
            league=r["league"]
            if league not in LEAGUES or r["season"]!="2025-26":continue
            names=lookups(league)
            h=names.get(norm(r["home"]));a=names.get(norm(r["away"]))
            ft=fulltime(r["ft_home"],r["ft_away"])
            day=scored_date(r["date"])
            if not h or not a or h==a or ft is None or not day or not (REFERENCE_SEASON_START<=day<=REFERENCE_SEASON_END):
                raise ValueError("BAD_RESEARCH_SOURCE_IDENTITY:"+league)
            k=(h,a)
            if k in result[league]:raise ValueError("DUPLICATE_RESEARCH_HOME_AWAY_PAIR:"+league)
            result[league][k]=(day,ft)
            sources[league][filename]+=1
    for lg,rows in result.items():
        expected=LEAGUES[lg]
        if len(rows)!=expected["expected"] or sum(score==(0,0) for _,score in rows.values())!=expected["zero"]:
            raise ValueError("FROZEN_RESEARCH_COUNT_OR_0_0_CHANGED:"+lg)
    return result,{x:dict(c) for x,c in sources.items()}

def get_csv(league):
    u=SOURCE+LEAGUES[league]["division"]+".csv"
    req=Request(u,headers={"User-Agent":"Mozilla/5.0 (onepass-historical-ft-facts-quality-audit/1.0)",
                           "Accept":"text/csv,application/csv;q=0.8"})
    with urlopen(req,timeout=25) as response:
        body=response.read(2_000_001)
        if len(body)>2_000_000:raise ValueError("EXTERNAL_SOURCE_TOO_LARGE")
    return body,u

def parse_external(league,raw):
    text=raw.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(io.StringIO(text,newline=""))
    if not {"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}.issubset(reader.fieldnames or []):
        raise ValueError("THIRD_SOURCE_REQUIRED_COLUMNS_MISSING")
    aliases=lookups(league)
    results={}; rawcount=0
    flags=Counter();unknown=Counter();zero=0;earliest=None;latest=None
    for r in reader:
        if not r.get("Date"):continue
        rawcount+=1
        if r.get("Div")!=LEAGUES[league]["division"]:
            raise ValueError("DIVISION_WRONG_IN_SOURCE")
        day=scored_date(r["Date"])
        if day is None:
            flags["BAD_DATE"]+=1;continue
        if day<REFERENCE_SEASON_START or day>REFERENCE_SEASON_END:
            flags["OUT_OF_SEASON"]+=1;continue
        if day>SECOND_SOURCE_COMPARE_CUTOFF:
            flags["LATER_OUTSIDE_FROZEN_COMPARE_CUTOFF"]+=1;continue
        h=aliases.get(norm(r.get("HomeTeam")));a=aliases.get(norm(r.get("AwayTeam")))
        if not h or not a:
            unknown[str(r.get("HomeTeam"))+" / "+str(r.get("AwayTeam"))]+=1
            flags["UNRECOGNIZED_CLUB_ALIAS"]+=1;continue
        ft=fulltime(r.get("FTHG"),r.get("FTAG"))
        if ft is None:
            flags["NO_NUMERIC_FT"]+=1;continue
        actual="H" if ft[0]>ft[1] else "A" if ft[0]<ft[1] else "D"
        if r.get("FTR") and r["FTR"]!=actual:
            raise ValueError("THIRD_SOURCE_FTR_SCORE_INCONSISTENT")
        k=(h,a)
        if k in results:raise ValueError("THIRD_SOURCE_DUPLICATE_PAIR")
        results[k]=(day,ft)
        zero+=ft==(0,0)
        earliest=day if earliest is None or day<earliest else earliest
        latest=day if latest is None or day>latest else latest
    if flags.get("UNRECOGNIZED_CLUB_ALIAS") and not results:
        raise ValueError("ALL_THIRD_SOURCE_TEAM_NAMES_UNRECOGNIZED")
    return results,{"raw_file_rows_with_date":rawcount,
        "scored_events_before_2025_11_20":len(results),
        "observed_0_0_scored_matches":zero,
        "min_date":earliest.isoformat() if earliest else None,
        "max_date":latest.isoformat() if latest else None,
        "flags":dict(flags),"unknown_club_sample":dict(unknown.most_common(10))}

def compare(league,primary_records,second_records,diag,source_url,sha):
    score_same=0;score_bad=0;absent=0;date_equal=0;date_diff=Counter()
    bad_examples=[];missing_examples=[]
    exact_z=0;bad_dates=[]
    for (home,away),(d,ft) in primary_records.items():
        independent=second_records.get((home,away))
        if not independent:
            absent+=1
            if len(missing_examples)<12:missing_examples.append({"home":home,"away":away,"original_date":d.isoformat()})
            continue
        date2,ft2=independent
        if ft==ft2:
            score_same+=1;exact_z+=ft==(0,0)
        else:
            score_bad+=1
            if len(bad_examples)<12:bad_examples.append({"home":home,"away":away,"original_FT":list(ft),"second_FT":list(ft2)})
        delta=(date2-d).days
        date_diff[str(delta)]+=1
        if delta==0:date_equal+=1
        elif len(bad_dates)<12:
            bad_dates.append({"home":home,"away":away,"original_day":d.isoformat(),"second_day":date2.isoformat(),"day_delta":delta,
                              "same_FT":ft==ft2})
    n=len(primary_records)
    full=(score_same==n and score_bad==0 and absent==0
          and not diag["flags"].get("UNRECOGNIZED_CLUB_ALIAS")
          and not diag["flags"].get("BAD_DATE")
          and diag["scored_events_before_2025_11_20"]>=n)
    return {"league":league,
      "expected_frozen_research_rows":n,
      "status":"ALL_SCORES_INDEPENDENTLY_MATCH" if full
               else "FAIL_CLOSED_UNRESOLVED_SCORE_OR_IDENTITY",
      "first_source":"OpenFootball CC0-claimed original 2025-26 scored data",
      "independent_url":source_url,"independent_csv_sha256":sha,
      "source_diagnostics":diag,"score_agreement":score_same,
      "0_0_original":sum(x[1]==(0,0) for x in primary_records.values()),
      "0_0_confirmed_second_source":exact_z,
      "score_conflict_count":score_bad,"missing_identity_count":absent,
      "exact_date_matches":date_equal,
      "dates_differ":sum(c for day,c in date_diff.items() if day!="0"),
      "date_delta_days_distribution":dict(sorted(date_diff.items(),key=lambda x:int(x[0]))),
      "score_conflict_examples":bad_examples,
      "missing_identity_examples":missing_examples,
      "date_disagreement_examples":bad_dates,
      "independent_kickoff_date_requires_separate_adjudication":bool(n-date_equal),
      "independent_result_source_model_training_rights":"NOT_ESTABLISHED",
      "source_match_data_rehosted":0,
      "training_rows_admitted":0,"source_research_rows_rewritten":0}
def audit():
    pinned,origins=primary()
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "frozen_2025_26_scope":["GER2","FRA2","ESP2"],
      "new_unchecked_research_score_keys":sum(len(x) for x in pinned.values()),
      "source_row_origin_counts":origins,
      "research_only":True,"bulk_external_CSV_copied_to_repo":False,
      "old_completed_league_score_QA_cases_repeated":0,
      "model_training_admissions":0,"main_M4_or_existing_seals_changed":False,
      "leagues":[]}
    for lg in ("GER2","FRA2","ESP2"):
        try:
            raw,url=get_csv(lg)
            results,diag=parse_external(lg,raw)
            report["leagues"].append(compare(lg,pinned[lg],results,diag,url,hashlib.sha256(raw).hexdigest()))
        except Exception as err:
            report["leagues"].append({"league":lg,"expected_frozen_research_rows":len(pinned[lg]),
                "status":"FAIL_CLOSED_SOURCE_OR_PARSER","error_class":type(err).__name__,
                "failure":str(err)[:160] if isinstance(err,ValueError) else "external_source_unavailable",
                "http_status":getattr(err,"code",None),
                "training_rows_admitted":0})
    return report

def selftest():
    p,src=primary()
    assert [len(p[k]) for k in ("GER2","FRA2","ESP2")]==[99,116,131]
    for lg in LEAGUES:
        assert len(LEAGUES[lg]["aliases"])==LEAGUES[lg]["clubs"]
        names=lookups(lg)
        assert all(norm(s) in names for s in LEAGUES[lg]["aliases"])
    assert lookups("GER2")[norm("Nurnberg")]=="1. FC Nürnberg"
    assert lookups("FRA2")[norm("St Etienne")]=="AS Saint-Étienne"
    assert lookups("ESP2")[norm("Dep. La Coruna")]=="Deportivo La Coruña"
    assert fulltime("0","0")==(0,0)
    assert fulltime("","")==None
    mock=("Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
          "D2,01/08/2025,Schalke 04,Hertha,2,1,H\n"
          "D2,02/08/2025,Elversberg,Nurnberg,1,0,H\n"
          "D2,03/08/2025,Kaiserslautern,Darmstadt,0,0,D\n").encode()
    data,diags=parse_external("GER2",mock)
    assert data[("FC Schalke 04","Hertha BSC")][1]==(2,1)
    assert data[("1. FC Kaiserslautern","SV Darmstadt 98")][1]==(0,0)
    print("PASS 99+116+131 pinned and 30 actual 0-0, alias dictionaries, synthetic FT and calendar")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--live",action="store_true")
    flags=parser.parse_args()
    if flags.self_test:selftest()
    if flags.live:
        print("THREE_LEAGUE_346_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("THREE_LEAGUE_346_END")
