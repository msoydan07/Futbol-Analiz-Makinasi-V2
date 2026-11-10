"""READ-ONLY ten-league source inventory and past-only opponent-strength diagnostic.

NO third-party downloads; NO production, M4 or original data writes.
Elo & matchday bins are exploratory descriptive strength proxies, NOT
proof of a tactical style or a trained goal probability predictor.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

EXPECTED_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
STAT_FIELDS=("home_shots","away_shots","home_shots_on_target","away_shots_on_target",
"home_corners","away_corners","home_yellow_cards","away_yellow_cards",
"home_red_cards","away_red_cards")
NOT_IN_ARCHIVE=("xG","shots location","passes","possession","pressing","PPDA",
"formations","lineups","match-state timings","coach tactics","player availability")
REQUIRED=("fixture_id","league","season","match_date","home_id","away_id","home_goals",
"away_goals","result","source_row","source_url")
BANDS=("away_150_plus","away_50_to_150","close_under_50",
        "home_50_to_150","home_150_plus")

class SourceBlocked(ValueError):pass

def read_rows(file):
    raw=Path(file).read_bytes()
    observed_sha=hashlib.sha256(raw).hexdigest()
    if observed_sha!=EXPECTED_SHA:raise SourceBlocked("SOURCE_BYTES_SHA_NOT_RESEARCH_ACCEPTED")
    reader=csv.DictReader(raw.decode("utf-8-sig").splitlines())
    header=set(reader.fieldnames or [])
    if set(REQUIRED)-header:raise SourceBlocked("REQUIRED_SCHEMA_COLUMNS_MISSING")
    rows=list(reader)
    if len(rows)!=4518:raise SourceBlocked("UNEXPECTED_ACCEPTED_4518_ROW_COUNT")
    if {r["league"] for r in rows}!=set(LEAGUES):raise SourceBlocked("UNEXPECTED_LEAGUE_COVERAGE")
    unique=set()
    for r in rows:
        fid=r["fixture_id"]
        if fid in unique:raise SourceBlocked("DUPLICATE_FIXTURE_ID")
        unique.add(fid)
        d=date.fromisoformat(r["match_date"])
        if d>date(2026,11,10):raise SourceBlocked("FUTURE_FINAL_SCORE_IN_ARCHIVE")
        if not r["home_id"] or not r["away_id"] or r["home_id"]==r["away_id"]:
            raise SourceBlocked("UNSAFE_CLUB_ID")
        h,a=int(r["home_goals"]),int(r["away_goals"])
        if h<0 or a<0 or r["result"]!=("H" if h>a else "A" if h<a else "D"):
            raise SourceBlocked("SCORE_RESULT_CONTRADICTION")
        if not r["source_url"].startswith("https://"):raise SourceBlocked("UNATTRIBUTED_SOURCE")
    return rows,header,observed_sha

def strength_band(diff):
    if diff<=-150:return BANDS[0]
    if diff<=-50:return BANDS[1]
    if diff<50:return BANDS[2]
    if diff<150:return BANDS[3]
    return BANDS[4]

def past_only_elo(rows):
    """Canonical league-local Elo. Same-date results NEVER inform one another."""
    ratings=defaultdict(lambda:1500.)
    observations=defaultdict(int)
    snapshots={}
    matches=defaultdict(list)
    for r in rows:matches[(r["league"],r["match_date"])].append(r)
    for (league,day),items in sorted(matches.items(),key=lambda x:(x[0][1],x[0][0])):
        pending=defaultdict(float)
        for r in items:
            kh,ka=(league,r["home_id"]),(league,r["away_id"])
            diff=ratings[kh]-ratings[ka]
            e=1/(1+10**(-(diff+65)/400))
            h,a=int(r["home_goals"]),int(r["away_goals"])
            outcome=1. if h>a else .5 if h==a else 0.
            delta=18*(outcome-e)
            if r["fixture_id"] in snapshots:raise SourceBlocked("DUPLICATE_ELO_SNAPSHOT")
            snapshots[r["fixture_id"]]={
                "league":league,"date":day,"season":r["season"],
                "band":strength_band(diff),"gap":diff,
                "home_pre_rating":ratings[kh],"away_pre_rating":ratings[ka],
                "home_prior_count":observations[kh],
                "away_prior_count":observations[ka]}
            pending[kh]+=delta
            pending[ka]-=delta
        for key,delta in pending.items():ratings[key]+=delta
        for r in items:
            observations[(league,r["home_id"])]+=1
            observations[(league,r["away_id"])]+=1
    if len(snapshots)!=len(rows):raise SourceBlocked("ELO_ASOF_COVERAGE_MISMATCH")
    return snapshots

def strength_metrics(rows,snapshots,by_league=False):
    groups=defaultdict(list)
    for r in rows:
        snap=snapshots[r["fixture_id"]]
        key=(r["league"],snap["band"]) if by_league else ("ALL",snap["band"])
        groups[key].append((r,snap))
    results={}
    for key,items in sorted(groups.items()):
        n=len(items)
        valid=[]
        for r,snap in items:
            hs,as_=r.get("home_shots"),r.get("away_shots")
            if hs not in ("",None) and as_ not in ("",None):
                try:
                    h,a=int(hs),int(as_)
                    if h>=0 and a>=0 and h+a>0:
                        valid.append(h/(h+a))
                except ValueError:pass
        results["/".join(key)]={
            "n":n,"n_with_both_teams_8plus_prior_matches":sum(
              min(s["home_prior_count"],s["away_prior_count"])>=8 for _,s in items),
            "home_goal_mean":round(sum(int(r["home_goals"]) for r,_ in items)/n,4),
            "away_goal_mean":round(sum(int(r["away_goals"]) for r,_ in items)/n,4),
            "home_win_rate":round(sum(r["result"]=="H" for r,_ in items)/n,4),
            "btts_rate":round(sum(int(r["home_goals"])>0 and int(r["away_goals"])>0 for r,_ in items)/n,4),
            "over25_rate":round(sum(int(r["home_goals"])+int(r["away_goals"])>=3 for r,_ in items)/n,4),
            "shot_share_n":len(valid),"home_shot_share_avg":round(sum(valid)/len(valid),4) if valid else None,
            "note":"Descriptive strength proxy; not game-state or formation data; all match scores already viewed."}
    return results

def audit(path):
    rows,columns,sha=read_rows(path)
    snaps=past_only_elo(rows)
    by_league={}
    for league in LEAGUES:
        ls=[r for r in rows if r["league"]==league]
        cells={}
        for field in STAT_FIELDS:
            ok=sum(r.get(field) not in ("",None) for r in ls)
            cells[field]={"available":ok,"missing":len(ls)-ok,"percent":round(ok/len(ls)*100,2)}
        seasons=dict(Counter(r["season"] for r in ls))
        latest=max(r["match_date"] for r in ls)
        by_league[league]={
            "n":len(ls),"seasons":seasons,"latest_scored_match":latest,
            "days_since_latest_on_2026_11_10":(date(2026,11,10)-date.fromisoformat(latest)).days,
            "unique_clubs":len({r["home_id"] for r in ls}|{r["away_id"] for r in ls}),
            "statistics":cells,
            "source_hosts":dict(Counter(r["source_url"].split("/")[2] for r in ls))}
    return {"schema":"263_OPPONENT_GOALS_TENLEAGUE_SOURCE_INVENTORY_V1",
      "status":"EXISTING_ACCEPTED_SOURCE_ONLY_NO_NEW_PROVIDER_DOWNLOAD",
      "snapshot_sha256":sha,"match_count":len(rows),
      "leagues":by_league,
      "fields_not_in_accepted_snapshot":list(NOT_IN_ARCHIVE),
      "opp_strength_elo_reference_assumptions":"Starting 1500 league-local each club; home +65; K=18; frozen before same-date results; no tuning; promoted team has cold start.",
      "opponent_strength_all":strength_metrics(rows,snaps),
      "opponent_strength_by_league":strength_metrics(rows,snaps,True),
      "limitations":[
        "The original 4518 history is owner-accepted for research and NOT independently verified match-by-match",
        "Dates are date-only; same-date result leakage prevented, but past matches' true kickoff time not known",
        "Elo groups cannot certify how any team would tactically play versus stronger opponents",
        "Shots and SoT are not xG; goals are not pre-match information for current fixture",
        "No xG, formations, pressing, player or exact match-state data in accepted history",
        "League-specific small slices are descriptive, not a selection rule",
        "Freshness must be renewed by identity-safe, legally usable data provenance; do not append unverified results",
        "No model parameters adjusted, no market probabilities or betting profitability implied"]}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",default="data/quad_accepted_263/extended_history.csv")
    a.add_argument("--out",required=True)
    args=a.parse_args()
    data=audit(args.source)
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if json.loads(p.read_text(encoding="utf8"))!=data:raise SourceBlocked("EXISTING_REPORT_MISMATCH")
    else:p.write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"count":data["match_count"],
       "leagues":{k:{"n":v["n"],"latest":v["latest_scored_match"],
                         "shots_pct":v["statistics"]["home_shots"]["percent"],
                         "sot_pct":v["statistics"]["home_shots_on_target"]["percent"]}
                  for k,v in data["leagues"].items()}},ensure_ascii=False))

if __name__=="__main__":main()
