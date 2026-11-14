#!/usr/bin/env python3
"""One new independent FT witness comparison ONLY for 207+99 GER2 ODbL novel facts.

No repeated old 99 CC0 / previous 871+904 audits.
Two light personal-research football-data.co.uk CSV requests only in memory.
Do not redistribute secondary source tables or use for training.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion/odbl_openligadb_germany2")
F25=ROOT/"ger2_2025_2026_207_novel_only_quarantine.csv"
F26=ROOT/"ger2_2026_2027_ODbL_research_quarantine.csv"
URLS={"2025-26":"https://www.football-data.co.uk/mmz4281/2526/D2.csv",
      "2026-27":"https://www.football-data.co.uk/mmz4281/2627/D2.csv"}
CUTOFF=date(2026,11,13)
EXPLICIT={
  "schalke 04":"fc schalke 04","schalke":"fc schalke 04",
  "bielefeld":"dsc arminia bielefeld","arminia bielefeld":"dsc arminia bielefeld",
  "furth":"spvgg greuther furth","greuther furth":"spvgg greuther furth",
  "dresden":"dynamo dresden","braunschweig":"eintracht braunschweig",
  "dusseldorf":"fortuna dusseldorf","duesseldorf":"fortuna dusseldorf",
  "munster":"preussen munster","muenster":"preussen munster",
  "paderborn":"sc paderborn 07","darmstadt":"sv darmstadt 98",
  "karlsruhe":"karlsruher sc","nurnberg":"1 fc nurnberg",
  "kaiserslautern":"1 fc kaiserslautern",
  "magdeburg":"1 fc magdeburg","bochum":"vfl bochum",
  "heidenheim":"1 fc heidenheim 1846",
  "osnabruck":"vfl osnabruck","osnabrueck":"vfl osnabruck",
  "elversberg":"sv 07 elversberg","hertha":"hertha bsc",
  "hannover":"hannover 96"
}
def norm(s):
    s=s.casefold().replace("ß","ss").replace("ü","u").replace("ä","a").replace("ö","o").replace("é","e")
    s="".join(c for c in unicodedata.normalize("NFKD",s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def alias(s):
    n=norm(s)
    return norm(EXPLICIT.get(n,n))
def parse_dt(s):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%d-%m-%Y","%Y-%m-%d"):
        try:return datetime.strptime(s.strip(),fmt).date()
        except ValueError:pass
    return None
def score(s):
    t=str(s or "").strip()
    if not re.fullmatch(r"\d{1,2}",t):return None
    num=int(t);return num if num<=30 else None
def old_source():
    r25=list(csv.DictReader(F25.open(encoding="utf-8",newline="")))
    r26=list(csv.DictReader(F26.open(encoding="utf-8",newline="")))
    if len(r25)!=207 or len(r26)!=99:raise ValueError("NOVEL_ONLY_306_SOURCE_COUNT_CHANGED")
    if {x["season"] for x in r25}!={"2025-26"} or {x["season"] for x in r26}!={"2026-27"}:
        raise ValueError("EXPECTED_HISTORICAL_SEASONS_ONLY")
    return {"2025-26":r25,"2026-27":r26}
def get(url):
    req=Request(url,headers={
     "User-Agent":"Mozilla/5.0 (FutbolAnalizMakinasi research score witness; one-off non-commercial light QA)",
     "Accept":"text/csv,application/csv;q=0.9"})
    with urlopen(req,timeout=30) as res:
        blob=res.read(1_700_001)
    if len(blob)>1_700_000 or b"<html" in blob[:150].lower():
        raise ValueError("SECOND_SOURCE_BAD_CSV_OR_TOO_LARGE")
    return blob
def independent(raw,season):
    t=io.StringIO(raw.decode("utf-8-sig",errors="replace"),newline="")
    reader=csv.DictReader(t)
    mandatory={"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}
    if not mandatory.issubset(reader.fieldnames or []):
        raise ValueError("INDEPENDENT_SOURCE_COLUMNS_MISSING")
    pairs={}
    flags=Counter()
    for r in reader:
        if r.get("Div")!="D2":continue
        day=parse_dt(r["Date"])
        if day is None:
            if not str(r.get("Date") or "").strip():continue
            raise ValueError("BAD_DATE_IN_SECOND_SOURCE")
        if season=="2025-26" and not date(2025,7,1)<=day<=date(2026,6,30):continue
        if season=="2026-27" and not date(2026,7,1)<=day<=CUTOFF:continue
        h,a=alias(r["HomeTeam"]),alias(r["AwayTeam"])
        hg,ag=score(r["FTHG"]),score(r["FTAG"])
        if hg is None or ag is None:
            flags["no_finished_ft"]+=1;continue
        key=(day.isoformat(),h,a)
        if key in pairs and pairs[key]!=(hg,ag):raise ValueError("DUPLICATE_SECOND_SOURCE_FT_CONFLICT")
        pairs[key]=(hg,ag)
        flags["mapped_date_home_away_ft"]+=1
    return pairs,dict(flags)
def evaluate():
    prim=old_source()
    totals=Counter();reports=[];groups={}
    for season,rows in prim.items():
        raw=get(URLS[season])
        ext,flags=independent(raw,season)
        counters=Counter();sample=defaultdict(list)
        for r in rows:
            key=(r["date"],alias(r["home"]),alias(r["away"]))
            got=ext.get(key)
            if got is None:
                verdict="SECOND_SOURCE_MISSING_OR_DATE_TEAM_UNRESOLVED"
            elif got==(int(r["ft_home"]),int(r["ft_away"])):
                verdict="SECOND_SOURCE_EXACT_DATE_HOME_AWAY_FT"
            else:
                verdict="SECOND_SOURCE_CONFLICT_FT"
            counters[verdict]+=1;totals[verdict]+=1
            if verdict!="SECOND_SOURCE_EXACT_DATE_HOME_AWAY_FT":
                # Do not export secondary competing score or tables.
                sample[verdict].append({"odbl_match_id":r["match_id"],"date":r["date"],
                                        "home":r["home"],"away":r["away"],
                                        "odbl_score":r["ft_home"]+"-"+r["ft_away"]})
        if sum(counters.values())!=len(rows):raise ValueError("GROUP_COUNTS_DRIFT")
        groups[season]={
          "ODbL_new_research_rows":len(rows),
          "second_FT_exact":counters["SECOND_SOURCE_EXACT_DATE_HOME_AWAY_FT"],
          "second_FT_conflict":counters["SECOND_SOURCE_CONFLICT_FT"],
          "second_unmatched":counters["SECOND_SOURCE_MISSING_OR_DATE_TEAM_UNRESOLVED"],
          "second_raw_SHA256":hashlib.sha256(raw).hexdigest(),
          "second_rows_parsed":flags,
          "unresolved_original_ODbL_records_only":dict(sample)
        }
    if sum(totals.values())!=306:raise ValueError("NEW_306_ONLY_DRIFT")
    return {"status":"GER2_NOVEL_306_TARGETED_SECOND_FT_FACT_WITNESS_COMPLETE",
      "checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "only_207_new_2025_and_99_new_2026":306,
      "earlier_99_2025_CC0_overlap_not_retested":True,
      "source_first":"OpenLigaDB original ODbL 1.0",
      "independent_source":"football-data.co.uk D2 historic match-result witness ONLY",
      "secondary_raw_scores_or_tables_rehosted":False,
      "secondary_2025_file":URLS["2025-26"],"secondary_2026_file":URLS["2026-27"],
      "totals":dict(totals),"by_season":groups,
      "old_2396_quarantine_changed":False,"old_296_holds_changed":False,
      "new_training_rows_approved":0,
      "main_M4_and_original_10_league_SHA_modified":False,
      "note":"Match fact check is not independent training license, immutable past as-of feature snapshot, nor whole-season completeness proof. Exact matches remain research-only."}
def selftest():
    assert alias("Arminia Bielefeld")==alias("DSC Arminia Bielefeld")
    assert alias("Nurnberg")==alias("1. FC Nürnberg")
    assert alias("Bochum")==alias("VfL Bochum")
    assert parse_dt("14/11/2026")==date(2026,11,14)
    assert score("0")==0 and score("") is None
    assert len(old_source()["2025-26"])==207
    assert len(old_source()["2026-27"])==99
    print("PASS original ODbL 306 source only, German aliases, preserve 0-0 scores and forbid blanks")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.live:
        try:report=evaluate()
        except Exception as e:report={"status":"FAIL_CLOSED_NO_NEW_TRAINING_OR_FT_CLAIM",
             "error_class":type(e).__name__,"reason":str(e)[:240] if isinstance(e,ValueError) else "external source unavailable",
             "new_training_rows_approved":0}
        print("GER2_NEW_306_START")
        print(json.dumps(report,indent=2,ensure_ascii=False))
        print("GER2_NEW_306_END")
