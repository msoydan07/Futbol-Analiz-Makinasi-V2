#!/usr/bin/env python3
"""ONE research-only aggregate audit, six leagues / nine league-seasons / 967 rows.

Only existing, Git-blob-pinned OpenFootball scored quarantine match facts are
evaluated. The prior 200 ENG3/ENG4 held fixture keys are excluded BEFORE
matching. Each external historical result CSV is requested at most once and
used IN MEMORY; no bulk results are rehosted, imported, trained or written.
Source rights, match-day date and historical as-of leakage remain independent
acceptance gates. No main M4, existing predictions or SHA seals modified.

Targets (2025/26 unless otherwise stated):
 ENG3 256, ENG4 176, ENG5 296, GRE1 62, SCO1 58;
 GRE1 2026/27 35, SCO1 2026/27 42, AUT1 2026/27 42.
 Six leagues, EIGHT league-season groups, 967 total.
"""
from __future__ import annotations
import argparse,csv,difflib,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from urllib.request import Request,urlopen
from prepare_2396_provenance_rights_quality_gate_20261114 import EXPECTED,HOLD,read_csv,match_key

TARGETS={
 "ENG3/2025-26":(256,"football-data","E2"),
 "ENG4/2025-26":(176,"football-data","E3"),
 "ENG5/2025-26":(296,"football-data","EC"),
 "GRE1/2025-26":(62,"football-data","G1"),
 "GRE1/2026-27":(35,"football-data","G1"),
 "SCO1/2025-26":(58,"football-data","SC0"),
 "SCO1/2026-27":(42,"football-data","SC0"),
 "AUT1/2026-27":(42,"matchdaysync","austrian-bundesliga")
}
# No current-year fallback to stale previous seasons.
URLS={
 key:("https://www.football-data.co.uk/mmz4281/"+("2526" if key.endswith("2025-26") else "2627")+"/"+code+".csv"
      if typ=="football-data" else
      "https://matchdaysync.com/api/public/csv/"+code+"/2026-27/matches")
 for key,(n,typ,code) in TARGETS.items()
}
MAX_DATE=date(2026,11,13)
# Explicit source aliases only; similarity does not automatically adjudicate.
CUSTOM={
 "ENG3":{
  "peterboro":"Peterborough United","peterborough":"Peterborough United",
  "plymouth":"Plymouth Argyle","mk dons":"Milton Keynes Dons",
  "port vale":"Port Vale FC",
 },
 "ENG4":{"mk dons":"Milton Keynes Dons",
         "accrington":"Accrington Stanley",
         "newport":"Newport County"},
 "ENG5":{"fc halifax":"Halifax Town","halifax":"Halifax Town",
         "forest green":"Forest Green Rovers","southend":"Southend United",
         "rochdale":"Rochdale AFC","solihull":"Solihull Moors"},
 "GRE1":{
  "aek":"AEK Athen","aek athens":"AEK Athen","aek athen":"AEK Athen",
  "aris":"Aris Saloniki","aris thessaloniki":"Aris Saloniki",
  "larisa":"AE Lárissa","larissa":"AE Lárissa","ael":"AE Lárissa",
  "kifisia":"AE Kifisias","kifissia":"AE Kifisias",
  "ofi":"OFI Heraklion","ofi crete":"OFI Heraklion",
  "olympiacos":"Olympiakos Piraeus","olympiakos":"Olympiakos Piraeus",
  "paok":"PAOK Saloniki","panetolikos":"Panetolikos",
  "asteras tripolis":"Asteras Tripolis","volos":"Volos NFC",
  "lamia":"Lamia","iraklis":"Iraklis 1908",
  },
 "SCO1":{"hearts":"Heart of Midlothian",
         "st mirren":"St. Mirren FC","st johnstone":"Saint Johnstone FC",
         "hibernian":"Hibernian FC",
         "falkirk":"Falkirk FC","livingston":"Livingston FC"},
 "AUT1":{
  "salzburg":"FC Salzburg","rb salzburg":"FC Salzburg",
  "red bull salzburg":"FC Salzburg",
  "austria vienna":"Austria Wien","fk austria wien":"Austria Wien",
  "a lustenau":"Austria Lustenau","austria lustenau":"Austria Lustenau",
  "lask":"LASK Linz","rapid":"Rapid Wien","sk rapid":"Rapid Wien",
  "sk rapid wien":"Rapid Wien","sturm graz":"Sturm Graz",
  "sk sturm graz":"Sturm Graz","ried":"SV Ried",
  "tirol":"WSG Tirol","hartberg":"TSV Hartberg",
  "wolfsberger ac":"Wolfsberger AC",
  "altach":"SCR Altach","grazer ak":"Grazer AK"
 }
}
def norm(x):
    value=str(x or "").casefold().replace("ß","ss").replace("ø","o").replace("æ","ae")
    value="".join(ch for ch in unicodedata.normalize("NFKD",value) if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]","",value)
def simplified(x):
    x=str(x or "").casefold().replace("ß","ss").replace("ø","o")
    x="".join(ch for ch in unicodedata.normalize("NFKD",x) if not unicodedata.combining(ch))
    x=re.sub(r"\b(?:afc|fc|sc|ss|sv|vfl|ud|as|usl)\b"," ",x)
    x=re.sub(r"\b(?:united|town|city|rovers|wanderers|county|athletic|stanley|albion)\b$"," ",x.strip())
    x=re.sub(r"[^a-z0-9]","",x)
    return x
def exact_name_maps(league,clubs):
    index={}
    collisions=set()
    for original in sorted(clubs):
        for k in (norm(original),simplified(original)):
            if k:
                if k in index and index[k]!=original:collisions.add(k)
                else:index[k]=original
    for key in collisions:index.pop(key,None)
    explicit={}
    for alt,canonical in CUSTOM.get(league,{}).items():
        # Only an alias to a club actually in this SOURCE season is valid.
        if canonical not in clubs:continue
        nk=norm(alt)
        if nk in explicit and explicit[nk]!=canonical:
            raise ValueError("CROSS_TEAM_ALIAS_CONFLICT")
        explicit[nk]=canonical
    for k,v in explicit.items():
        if k in index and index[k]!=v:raise ValueError("ALIAS_OVERWRITES_ANOTHER_CLUB")
        index[k]=v
    return index
def match_name(raw,table):
    n=norm(raw)
    if n in table:return table[n]
    s=simplified(raw)
    return table.get(s)
def day_of(text):
    s=str(text or "").strip()
    for fmt in ("%d/%m/%y","%d/%m/%Y","%d-%m-%y","%d-%m-%Y","%Y-%m-%d"):
        try:return datetime.strptime(s,fmt).date()
        except ValueError:pass
    return None
def score(home,away):
    a,b=str(home or "").strip(),str(away or "").strip()
    if not re.fullmatch(r"\d{1,2}",a) or not re.fullmatch(r"\d{1,2}",b):return None
    x,y=int(a),int(b)
    return (x,y) if x<=30 and y<=30 else None
def pinned_primary():
    hold,hashcode=read_csv(HOLD)
    held={match_key(row) for row in hold}
    if len(held)!=200:raise ValueError("HOLD_200_KEYS_CHANGED")
    rows={k:{} for k in TARGETS};by_source=defaultdict(Counter);clubs=defaultdict(set)
    for filename,(source_hash,n,tag) in EXPECTED.items():
        if tag!="PUBLISHER_CC0_CLAIM":continue
        data,sha=read_csv(filename)
        if sha!=source_hash or len(data)!=n:raise ValueError("ORIGINAL_SOURCE_CHANGED:"+filename)
        for r in data:
            key=r["league"]+"/"+r["season"]
            if key not in TARGETS:continue
            if match_key(r) in held:continue
            d=day_of(r["date"]);ft=score(r["ft_home"],r["ft_away"])
            if not d or not ft or d>MAX_DATE:raise ValueError("PRIMARY_INVALID_DATE_SCORE")
            fixture=(r["home"],r["away"])
            if fixture in rows[key]:raise ValueError("PRIMARY_DUPLICATE_PAIR:"+key)
            rows[key][fixture]=(d,ft)
            clubs[key].update(fixture)
            by_source[key][filename]+=1
    if sum(map(len,rows.values()))!=967:raise ValueError("OVERALL_TARGETS_NOT_967")
    for key,(expected,typ,code) in TARGETS.items():
        if len(rows[key])!=expected:raise ValueError("SOURCE_KEY_COUNT_DRIFT:"+key)
    return rows,clubs,{k:dict(v) for k,v in by_source.items()}
def fetch(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (one-batch-historic-facts-audit/1.0)",
                             "Accept":"text/csv,application/csv;q=0.8"})
    with urlopen(req,timeout=24) as res:
        blob=res.read(2_000_001)
        if len(blob)>2_000_000:raise ValueError("CSV_RESPONSE_OVER_LIMIT")
    if b"<html" in blob[:150].lower():raise ValueError("HTML_RETURNED_NOT_CSV")
    return blob
def external_csv(raw,group,clubs):
    league,season=group.split("/")
    typ=TARGETS[group][1]
    src=io.StringIO(raw.decode("utf-8-sig",errors="replace"),newline="")
    reader=csv.DictReader(src)
    needed={"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"} if typ=="football-data" else {"date","status","home","away","home_goals","away_goals"}
    if not needed.issubset(reader.fieldnames or []):
        raise ValueError("SECONDARY_SOURCE_HEADERS_UNKNOWN:"+repr(reader.fieldnames[:15] if reader.fieldnames else None))
    index=exact_name_maps(league,clubs)
    mapped={};flags=Counter();examples=defaultdict(list);rawcount=0;unique_names=set()
    for r in reader:
        if typ=="football-data":
            if not r.get("Date"):continue
            if r.get("Div")!=TARGETS[group][2]:
                flags["unexpected_division"]+=1;continue
            day=day_of(r.get("Date"))
            rh,ra=r.get("HomeTeam"),r.get("AwayTeam")
            ft=score(r.get("FTHG"),r.get("FTAG"))
            if r.get("FTR") and ft is not None:
                result="H" if ft[0]>ft[1] else "A" if ft[0]<ft[1] else "D"
                if r["FTR"]!=result:raise ValueError("FTR_SCORE_CONFLICT")
        else:
            if str(r.get("status","")).lower().strip() not in ("finished","completed","full-time","full time","ft"):
                flags["not_finished"]+=1;continue
            day=day_of(str(r.get("date") or "")[:10])
            rh,ra=r.get("home"),r.get("away")
            ft=score(r.get("home_goals"),r.get("away_goals"))
        rawcount+=1
        if day is None or day<date(2025,7,1) or day>MAX_DATE:
            flags["invalid_date_outside_window"]+=1;continue
        if season=="2025-26" and not day<date(2026,7,1):continue
        if season=="2026-27" and not day>=date(2026,7,1):continue
        if ft is None:
            flags["unscored"]+=1;continue
        h=match_name(rh,index);a=match_name(ra,index)
        if h is None or a is None or h==a:
            flags["unmapped_team_or_same"]+=1
            if len(examples["unmapped"])<10:
                examples["unmapped"].append({"home":str(rh),"away":str(ra),"date":day.isoformat()})
            continue
        pair=(h,a)
        unique_names.update([h,a])
        if pair in mapped:
            if mapped[pair]!=(day,ft):
                flags["duplicate_pair_with_date_or_score_difference"]+=1
                if len(examples["duplicate"])<8:examples["duplicate"].append(
                    {"home":h,"away":a,"day":day.isoformat(),"original_day":mapped[pair][0].isoformat(),
                     "same_score":mapped[pair][1]==ft})
            else:flags["redundant_alias_exact_duplicate"]+=1
            continue
        mapped[pair]=(day,ft)
    return mapped,{"physical_source_rows_read":rawcount,"unique_canonical_scored_pairs":len(mapped),
      "unique_canonical_clubs":len(unique_names),"flags":dict(flags),
      "issue_examples":dict(examples),"confirmed_zero_zero_in_source":sum(ft==(0,0) for day,ft in mapped.values())}
def compare(group,original,secondary,diagnostics,sha):
    confirmed=0;score_only=0;score_conflict=0;not_found=0;date_delta=Counter()
    zero=0;examples=defaultdict(list)
    for (home,away),(day,ft) in original.items():
        got=secondary.get((home,away))
        if got is None:
            not_found+=1
            if len(examples["absent"])<9:examples["absent"].append({"home":home,"away":away})
            continue
        other_day,other_ft=got
        delta=(other_day-day).days
        date_delta[str(delta)]+=1
        if ft!=other_ft:
            score_conflict+=1
            if len(examples["score_conflict"])<10:examples["score_conflict"].append({
                "home":home,"away":away,"date":day.isoformat(),"primary_score":list(ft),"independent_score":list(other_ft)})
        elif delta:
            score_only+=1
            if len(examples["different_date"])<10:examples["different_date"].append({
                "home":home,"away":away,"primary_date":day.isoformat(),"secondary_date":other_day.isoformat(),
                "days":delta})
        else:confirmed+=1
        if ft==(0,0) and other_ft==ft:zero+=1
    group_n=len(original)
    passed=(confirmed==group_n and not score_only and not score_conflict and not not_found
            and diagnostics["flags"].get("duplicate_pair_with_date_or_score_difference",0)==0)
    return {"group":group,"league":group.split("/")[0],"season":group.split("/")[1],
       "research_candidates":group_n,
       "status":"ALL_DATE_TEAM_FT_PASS" if passed else "PARTIAL_OR_BLOCKED_DO_NOT_PROMOTE",
       "exact_date_team_FT_confirmed":confirmed,
       "score_matches_but_date_disagrees":score_only,
       "source_FT_disagreement":score_conflict,
       "second_source_fixture_not_identified":not_found,
       "zero_zero_independently_confirmed":zero,
       "source_sha256":sha,"source_url":URLS[group],
       "source_diagnostics":diagnostics,
       "date_delta_distribution":dict(sorted(date_delta.items(),key=lambda kv:int(kv[0]))),
       "exceptions_sample_max10":dict(examples),
       "source_training_rights":"NOT_APPROVED_FOR_MODEL_REUSE",
       "training_admitted":0}
def run():
    originals,clubs,files=pinned_primary()
    report={"run_at_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"SIX_LEAGUES_EIGHT_SEASON_GROUPS_967_NEW_CC0_CLAIMED_RESEARCH_FT_FACTS",
      "six_leagues":["ENG3","ENG4","ENG5","GRE1","SCO1","AUT1"],
      "source_group_count":len(TARGETS),"candidate_count":967,
      "original_source_distribution":files,
      "earlier_904_match_score_QA_repeated":0,
      "existing_200_ENG3_ENG4_original_problem_keys_excluded":True,
      "new_training_admissions":0,
      "original_quarantine_modified":False,
      "production_M4_prediction_SHA_changed":False,
      "external_csv_rehosted":False,
      "groups":[]}
    for group in TARGETS:
        try:
            raw=fetch(URLS[group])
            data,diag=external_csv(raw,group,clubs[group])
            result=compare(group,originals[group],data,diag,hashlib.sha256(raw).hexdigest())
        except Exception as exc:
            result={"group":group,"league":group.split("/")[0],"season":group.split("/")[1],
               "research_candidates":len(originals[group]),"status":"FAIL_CLOSED_UNAVAILABLE_OR_UNPARSEABLE",
               "source_url":URLS[group],"error_class":type(exc).__name__,
               "http_status":getattr(exc,"code",None),
               "reason":str(exc)[:180] if isinstance(exc,ValueError) else "external source unavailable",
               "training_admitted":0}
        report["groups"].append(result)
    sums={k:sum(g.get(k,0) for g in report["groups"]) for k in
       ("research_candidates","exact_date_team_FT_confirmed","score_matches_but_date_disagrees",
        "source_FT_disagreement","second_source_fixture_not_identified","zero_zero_independently_confirmed")}
    sums["full_pass_groups"]=sum(g["status"]=="ALL_DATE_TEAM_FT_PASS" for g in report["groups"])
    sums["unresolved_or_unchecked"]=967-sums["exact_date_team_FT_confirmed"]
    sums["approved_training_rows"]=0
    report["totals"]=sums
    return report

def selftest():
    original,clubs,filenames=pinned_primary()
    assert len(TARGETS)==8 and len(original)==8 and sum(map(len,original.values()))==967
    assert len({k.split("/")[0] for k in TARGETS})==6
    assert norm("Cádiz CF")=="cadizcf"
    assert match_name("Plymouth",exact_name_maps("ENG3",clubs["ENG3/2025-26"]))=="Plymouth Argyle"
    assert match_name("Bolton",exact_name_maps("ENG3",clubs["ENG3/2025-26"]))=="Bolton Wanderers"
    assert match_name("Hearts",exact_name_maps("SCO1",clubs["SCO1/2025-26"]))=="Heart of Midlothian"
    assert score("0","0")==(0,0) and score("","") is None
    sample=("Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
        "E2,01/08/2025,Luton,Wimbledon,1,0,H\n"
        "E2,02/08/2025,Bolton,Peterboro,0,0,D\n").encode()
    x,d=external_csv(sample,"ENG3/2025-26",clubs["ENG3/2025-26"])
    assert x[("Luton Town","AFC Wimbledon")][1]==(1,0),(x,d)
    assert x[("Bolton Wanderers","Peterborough United")][1]==(0,0)
    print("PASS eight season groups and 967 frozen rows, 200 holds excluded, historical aliases and zero-vs-blank")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true")
    opt=p.parse_args()
    if opt.self_test:selftest()
    if opt.live:
        print("SIX_LEAGUE_967_START")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SIX_LEAGUE_967_END")
