#!/usr/bin/env python3
"""Research-only ODbL rights-separated 2026/27 source availability probe.
Attribution: Daten von OpenLigaDB (www.openligadb.de), lizenziert unter ODbL 1.0.
No full raw result sets persisted, no models trained, no upstream content copied.
"""
import datetime, hashlib, json, re
import urllib.request
from collections import Counter

BASE="https://api.openligadb.de"
MAX_BYTES=12_000_000

def fetch(path):
    url=BASE+path
    req=urllib.request.Request(url,headers={
        "Accept":"application/json","User-Agent":"ResearchOnlyFixtureLicenceAudit/1.0 (one pass, cache results)"
    })
    with urllib.request.urlopen(req,timeout=22) as r:
        data=r.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES: raise ValueError("SOURCE_TOO_LARGE")
        if "json" not in r.headers.get("Content-Type","").lower(): raise ValueError("NOT_JSON")
    return json.loads(data),hashlib.sha256(data).hexdigest()

def ft(m):
    r=m.get("matchResults") or []
    if not isinstance(r,list) or m.get("matchIsFinished") is not True:return None
    values=[(x.get("pointsTeam1"),x.get("pointsTeam2")) for x in r
            if isinstance(x,dict) and x.get("resultTypeID",x.get("resultTypeId"))==2]
    if len(values)!=1:return None
    h,a=values[0]
    if type(h)!=int or type(a)!=int or not(0<=h<=30 and 0<=a<=30):return None
    return h,a

def analyze(name,shortcut,records,sha):
    if not isinstance(records,list):raise ValueError("NON_ARRAY_SEASON")
    accepted={}; reasons=Counter(); clubset=set(); late=0; zero=0
    for m in records:
        if not isinstance(m,dict):reasons["invalid_shape"]+=1;continue
        if m.get("matchIsFinished") is not True:reasons["unfinished"]+=1;continue
        dt=str(m.get("matchDateTime") or m.get("matchDateTimeUTC") or "")[:10]
        try: d=datetime.date.fromisoformat(dt)
        except ValueError:reasons["bad_date"]+=1;continue
        if not(datetime.date(2026,7,1)<=d<=datetime.date(2026,11,13)):
            reasons["out_of_window"]+=1;continue
        h=(m.get("team1") or {}).get("teamName","")
        a=(m.get("team2") or {}).get("teamName","")
        score=ft(m)
        if not h or not a or h==a or score is None:
            reasons["identity_or_ft_missing"]+=1;continue
        key=(dt,h,a)
        if key in accepted:
            reasons["duplicate"]+=1
            if accepted[key]!=score: reasons["duplicate_conflicting_score"]+=1
            continue
        accepted[key]=score
        clubset.update((h,a))
        zero+=int(score==(0,0))
    return {
       "league":name,"shortcut":shortcut,"raw_match_rows":len(records),
       "sha256":sha,"valid_unique_finished_FT_before_Nov14":len(accepted),
       "valid_unique_clubs":len(clubset),"goals":sum(h+a for h,a in accepted.values()),
       "zero_zero_matches":zero,
       "last_date":max((k[0] for k in accepted),default=None),
       "exclusions":dict(reasons),"license":"ODbL-1.0; separate sharealike and attribution required",
       "source_quality_gate":"FULL_COVERAGE_CANDIDATE" if len(accepted)==(78 if name=="CHE1" else 84) else "NOT_FULL_SEASON_TO_DATE",
       "source_links":{"api":BASE+f"/getmatchdata/{shortcut}/2026","license":"https://www.openligadb.de/en/license"},
       "eligible_for_training":False,
       "rows_saved":0
    }

def main():
    report={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "rights_source":"OpenLigaDB ODbL 1.0", "source_rows_saved":0, "trainable_rows_added":0, "production_untouched":True,
            "sources":[],"denmark_candidates":[],"discovery_status":""}
    try:
        leagues,sha=fetch("/getavailableleagues/2026")
        assert isinstance(leagues,list)
        for entry in leagues:
            shortcut=str(entry.get("leagueShortcut",""))
            name=str(entry.get("leagueName",""))
            if re.search("d[aä]n|denmark|superliga",name,re.I) or (shortcut.lower() in {"dk1","dnk1","dks","sl1"}):
                report["denmark_candidates"].append({"shortcut":shortcut,"league_name":name,"season":entry.get("leagueSeason")})
        report["league_list_sha256"]=sha
        report["league_list_count"]=len(leagues)
        report["discovery_status"]="SUCCESS"
    except Exception as exc:
        report["discovery_status"]=type(exc).__name__
    tested={"bsl"}
    for label,shortcut in [("CHE1","bsl")]+[("DNK1",x["shortcut"]) for x in report["denmark_candidates"][:4]]:
        if not shortcut or (label=="DNK1" and shortcut in tested):continue
        tested.add(shortcut)
        try:
            records,sha=fetch("/getmatchdata/"+shortcut+"/2026")
            report["sources"].append(analyze(label,shortcut,records,sha))
        except Exception as exc:
            report["sources"].append({"league":label,"shortcut":shortcut,"status":"UNAVAILABLE",
                                      "error_class":type(exc).__name__,"rows_saved":0})
    print("ODBL_SOURCE_PROBE_START")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    print("ODBL_SOURCE_PROBE_END")

if __name__=="__main__":main()
