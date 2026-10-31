"""Diagnose xG unmatched rows without making any new fixture matches.

Uses the same historical fixture/candidate tables as audit_understat_xg.py.
Reports exact team/date/score evidence; suggests nothing automatically.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from audit_understat_xg import norm

def rows(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def classify(args):
    hist=rows(args.historical)
    candidates=rows(args.candidates)
    source=rows(args.source)
    audit=rows(args.audit)
    candidate_index={(r["league"],r["season"],r["source_row"]):r for r in candidates}
    by_group=defaultdict(list)
    for h in hist:
        c=candidate_index.get((h["league"],h["season"],h["source_row"]))
        if c:
            by_group[(h["league"],h["season"])].append({
                "date":date.fromisoformat(h["match_date"][:10]),
                "home":norm(c["home"]),"away":norm(c["away"]),
                "score":(int(h["home_goals"]),int(h["away_goals"])),
                "fixture_id":h["fixture_id"]})
    results=[]
    totals=Counter()
    for a in audit:
        if a["status"]!="UNMATCHED":
            continue
        pos=int(a["source_row"])-2
        if pos<0 or pos>=len(source):
            raise ValueError("Audit/source row mismatch")
        r=source[pos]
        if any(str(a[k])!=str(r[k]) for k in ("league","season","home_team","away_team")):
            raise ValueError("Audit/source order mismatch at row "+a["source_row"])
        group=by_group[(r["league"],r["season"])]
        d=date.fromisoformat(r["match_date"][:10])
        home,away=norm(r["home_team"]),norm(r["away_team"])
        score=(int(r["home_goals"]),int(r["away_goals"]))
        same_names=[m for m in group if (m["home"],m["away"])==(home,away)]
        same_day=[m for m in group if m["date"]==d]
        close_names=[m for m in same_names if abs((m["date"]-d).days)<=2]
        same_day_score=[m for m in same_day if m["score"]==score]
        if same_names:
            if any(m["date"]==d for m in same_names):
                category="EXACT_NAMES_DATE_BUT_NOT_MATCHED"
            elif close_names:
                category="DATE_OFFSET_WITHIN_2_DAYS"
            else:
                category="DATE_MISMATCH_OR_WRONG_SEASON"
        elif same_day_score:
            category="POSSIBLE_TEAM_NAME_DIFFERENCE"
        elif same_day:
            category="SAME_DAY_NO_NAME_OR_SCORE_EVIDENCE"
        else:
            category="NO_HISTORICAL_MATCH_DATE"
        totals[(r["league"],r["season"],category)]+=1
        results.append({"source_row":a["source_row"],"league":r["league"],"season":r["season"],
            "match_date":r["match_date"],"home_team":r["home_team"],"away_team":r["away_team"],
            "score":f"{score[0]}-{score[1]}","category":category,
            "same_names_count":len(same_names),"same_day_count":len(same_day),
            "same_day_same_score_count":len(same_day_score),
            "near_date_same_names_count":len(close_names)})
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    with open(args.output,"w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]) if results else
            ["source_row","league","season","match_date","home_team","away_team","score","category",
             "same_names_count","same_day_count","same_day_same_score_count","near_date_same_names_count"])
        writer.writeheader()
        writer.writerows(results)
    summary={"unmatched_total":len(results),"classification":[
        {"league":l,"season":s,"category":c,"count":n}
        for (l,s,c),n in sorted(totals.items())],
        "warning":"Categories are diagnostic evidence only, not approved fixture joins."}
    Path(args.report).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--historical",default="data/historical_results.csv")
    p.add_argument("--candidates",default="data/fixture_candidates.csv")
    p.add_argument("--source",default="data/understat_matches.csv")
    p.add_argument("--audit",default="data/understat_xg_match_audit.csv")
    p.add_argument("--output",default="data/understat_unmatched_diagnosis.csv")
    p.add_argument("--report",default="data/understat_unmatched_diagnosis.json")
    classify(p.parse_args())
