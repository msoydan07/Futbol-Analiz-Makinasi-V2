"""Next non-repeated job: explain goal/BTTS forecast errors from REAL pre-match M4 seals.

Novel targeted diagnostic, not a repeat of the old 984 historical M4 refit.
- Original Nov 8 pre-kickoff SHA-locked M4 goal rates: 40 entries.
- Existing later web-reviewed results: 39, 1 postponed (NOT official final-ID attested).
- Historical accepted 4518 games ONLY for past-only rival Elo and historical
  league climate baseline; no future-score feature leakage.
- Goal-error split home/away, 2.5 over & BTTS per league and opponent power,
  compared against the simple prior same-league 2026/27 frequency baseline.
- Does not change M4, calibrate p, approve results or bet on outcomes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,date,timezone
from pathlib import Path

from data_opponent_goal_audit import read_rows,strength_band

BATCH=("new100_42469245388.json","new100_42469487639.json")
ROOT_HISTORY="data/quad_accepted_263/extended_history.csv"
MARKETS=("BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")
EXPECTED_DATE="2026-11-08"
class AuditStop(ValueError):pass

def require(x,msg):
    if not x:raise AuditStop(msg)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def digest(payload):
    base={k:v for k,v in payload.items() if k!="payload_sha256"}
    return hashlib.sha256(json.dumps(base,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def aware(s):
    t=datetime.fromisoformat(s.replace("Z","+00:00"))
    require(t.tzinfo is not None,"NAIVE_DATE_REJECTED")
    return t.astimezone(timezone.utc)

def history_snapshot(root):
    data,_,sha=read_rows(root/ROOT_HISTORY)
    require(len(data)==4518 and sha=="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9",
            "ACCEPTED_HISTORY_HASH_MISMATCH")
    require(all(r["match_date"]<EXPECTED_DATE for r in data),"POST_MATCH_HISTORY_LEAKAGE")
    return data,sha

def league_climate(history):
    """Baseline: actual SAME LEAGUE current-season games before Nov 8 only."""
    group=defaultdict(list)
    for r in history:
        if r["season"]=="2026-2027":
            group[r["league"]].append(r)
    result={}
    for league,rows in group.items():
        n=len(rows)
        require(n>=35,"NOT_ENOUGH_PRIOR_CURRENT_LEAGUE_HISTORY")
        vals={market:sum(
            (int(r["home_goals"])>0 and int(r["away_goals"])>0) if market=="BTTS_YES" else
            (int(r["home_goals"])+int(r["away_goals"])>float(market.removeprefix("OVER_")))
            for r in rows)/n for market in MARKETS}
        result[league]={"n":n,"rates":vals,"latest_date":max(r["match_date"] for r in rows)}
    require(len(result)==10,"TEN_LEAGUE_PRIOR_CLIMATE_MISSING")
    return result

def end_ratings_before_nov8(history):
    """FROZEN before match date, same-date games cannot inform each other."""
    grouped=defaultdict(list)
    for r in history:grouped[(r["league"],r["match_date"])].append(r)
    ratings=defaultdict(lambda:1500.)
    seen=Counter()
    for (league,day),rows in sorted(grouped.items(),key=lambda z:(z[0][1],z[0][0])):
        require(day<EXPECTED_DATE,"ELO_FUTURE_MATCH_LEAK")
        deltas=defaultdict(float)
        for r in rows:
            hk,ak=(league,r["home_id"]),(league,r["away_id"])
            e=1/(1+10**(-(ratings[hk]-ratings[ak]+65)/400))
            y=1 if r["result"]=="H" else .5 if r["result"]=="D" else 0
            delta=18*(y-e)
            deltas[hk]+=delta;deltas[ak]-=delta
        for k,d in deltas.items():ratings[k]+=d
        for r in rows:
            seen[(league,r["home_id"])]+=1
            seen[(league,r["away_id"])]+=1
    return ratings,seen

def read_original_seals(root):
    out={}
    for name in BATCH:
        b=read(root/"experiments/263/sabah_batch_reports"/name)
        require(b["schema"]=="SABAH_TOPLU_KAYIT_V1" and b["cohort"]=="new100"
                and b["day_turkey"]==EXPECTED_DATE,"BATCH_IS_NOT_NOV8")
        require(b.get("payload_sha256")==digest(b),"BATCH_HASH_TAMPERED")
        for r in b["outcomes"]:
            if r["status"]!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            key=(r["league"],r["home"],r["away"])
            require(key not in out,"DUPLICATE_NOV8_SEAL")
            path=r["forecast_path"]
            require(bool(re.fullmatch(r"forward_morning_263/2026-11-08/[a-f0-9]{24}\.json",path)),
                     "UNTRUSTED_SEAL_PATH")
            f=read(root/path)
            require(f.get("payload_sha256")==digest(f)==r["forecast_sha256"],"FORECAST_SHA_TAMPERED")
            fx=f["fixture"]
            require(fx["league"]==r["league"] and fx["kickoff_utc"]==r["kickoff_utc"]
                    and fx["match_local_date"]==EXPECTED_DATE
                    and fx["fixture_verification"]=="VERIFIED_BY_LIVE_OFFICIAL_GATE",
                    "WRONG_FIXTURE_OR_VERIFICATION")
            require(aware(f["created_at_utc"])<aware(fx["kickoff_utc"]),"FORECAST_AFTER_KICKOFF")
            require(fx["home_id"]!=fx["away_id"],"SAME_TEAM")
            out[key]=f
    require(len(out)==40,"NOV8_40_LOCKED_FORECASTS_REQUIRED")
    return out

def score(p,y):
    require(type(p) in (float,int) and math.isfinite(p) and 0<=p<=1,"INVALID_PROBABILITY")
    return (p-y)**2

def explain(root):
    root=Path(root)
    historical,history_sha=history_snapshot(root)
    rate=league_climate(historical)
    rating,prior=end_ratings_before_nov8(historical)
    forecasts=read_original_seals(root)
    review=read(root/"experiments/263/nov8_webreview_results_263.json")
    require(review["schema"]=="263_NOV8_WEB_REVIEW_RESEARCH_ONLY_V1" and
            review["new100_accepted_results"]==0 and
            review["day_turkey"]==EXPECTED_DATE,"NOV8_WEB_REVIEW_ONLY_REQUIRED")
    observations={}
    for r in review["rows"]:
        key=(r["league"],r["home"],r["away"])
        require(key not in observations,"DUPLICATE_WEB_SCORE")
        require(r["source_class"] in (
            "PRIMARY_LEAGUE_OR_CLUB","MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL"),
            "UNEXPECTED_SOURCE_QUALITY")
        if r["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL":
            require(bool(r.get("crosscheck_url")),"NO_MEDIA_CROSSCHECK")
        observations[key]=r
    require(set(forecasts)==set(observations),"FORECAST_VS_WEB_SCORE_NAME_JOIN_INCOMPLETE")
    rows=[];no_m4=Counter();postponed=0
    for key,f in sorted(forecasts.items()):
        outcome=observations[key]
        if outcome["status"]=="POSTPONED":
            postponed+=1;continue
        require(outcome["status"]=="FULL_TIME","NONFINAL_WEB_SCORE")
        home,away=int(outcome["home_goals"]),int(outcome["away_goals"])
        require(0<=home<=20 and 0<=away<=20,"IMPOSSIBLE_GOALS")
        mdl=f["model_predictions"]["M4"]
        if mdl["status"]!="AVAILABLE":
            no_m4[key[0]]+=1;continue
        goals=mdl["goals"]
        require(goals["distribution"]=="independent_poisson","EXPECTED_LOCKED_M4_ONLY")
        lamh,lama=goals["lambda_home"],goals["lambda_away"]
        require(all(type(v) in (int,float) and math.isfinite(v) and 0<v<=8 for v in (lamh,lama)),
                "IMPOSSIBLE_LAMBDA")
        markets=goals["markets"]
        require(abs(sum(markets["1X2"].values())-1)<1e-8,
                "M4_MS_VECTOR_BAD")
        fx=f["fixture"]
        hkey,akey=(fx["league"],fx["home_id"]),(fx["league"],fx["away_id"])
        gap=rating[hkey]-rating[akey]
        event={"BTTS_YES":int(home>0 and away>0),
               "OVER_1.5":int(home+away>=2),
               "OVER_2.5":int(home+away>=3),
               "OVER_3.5":int(home+away>=4)}
        ps={k:float(markets[k]) for k in MARKETS}
        require(all(0<=v<=1 and math.isfinite(v) for v in ps.values()),
                "M4_INVALID_GOAL_MARKETS")
        rows.append({
            "league":fx["league"],
            "strength_band":strength_band(gap),
            "both_team_prior_8plus":min(prior[hkey],prior[akey])>=8,
            "source_class":outcome["source_class"],
            "home_goal_error":home-lamh,
            "away_goal_error":away-lama,
            "total_goal_error":home+away-lamh-lama,
            "events":event,"probabilities":ps,
            "league_baseline":rate[fx["league"]]["rates"],
            "league_baseline_n":rate[fx["league"]]["n"]
        })
    require(postponed==1 and len(rows)+sum(no_m4.values())==39,
            "RESEARCH_NOV8_COHORT_NOT_LOCKED_39_PLUS_POSTPONED")
    return {"schema":"263_NOV8_SEALED_M4_GOAL_MATCHUP_ERROR_DIAG_V1",
        "status":"DESCRIPTIVE_39_RESEARCH_ONLY_NOT_INDEPENDENT_CALIBRATION",
        "forecast_sha_locked":40,"postponed_excluded":postponed,"scored_m4":len(rows),
        "nonavailable_m4":dict(no_m4),
        "source_class_counts":dict(Counter(r["source_class"] for r in rows)),
        "accepted_past_history_sha256":history_sha,
        "same_match_date_goal_data_used_in_model_features":False,
        "league_current_season_baselines":rate,
        "whole":summarize(rows),
        "only_primary_pages":summarize([r for r in rows if r["source_class"]=="PRIMARY_LEAGUE_OR_CLUB"]),
        "by_league":{x:summarize([r for r in rows if r["league"]==x]) for x in sorted({r["league"] for r in rows})},
        "by_elo_strength":{x:summarize([r for r in rows if r["strength_band"]==x]) for x in (
            "away_150_plus","away_50_to_150","close_under_50","home_50_to_150","home_150_plus")},
        "by_both_teams_prior_8_matches":{
          "yes":summarize([r for r in rows if r["both_team_prior_8plus"]]),
          "no":summarize([r for r in rows if not r["both_team_prior_8plus"]])},
        "negative_conclusions":[
          "This research web review is not independent federation fixture-ID attestation",
          "39 scores on one calendar day cannot certify any 70% event or future calibration",
          "Strength band is past-only league-local Elo proxy, NOT observed tactical low block/press",
          "League baseline uses 2026-27 completed games strictly BEFORE Nov 8; not a matched-lambda sophisticated model",
          "Prior 984 retrospective matches were NOT refitted or re-evaluated",
          "No M4 model or 4518/4617 dataset change, no 99 candidates used, no odds or betting inference"
        ],
        "model_changed":False,"seals_changed":False,"production_accepted_rows":4518}

def summarize(rows):
    n=len(rows)
    out={"n":n,
         "reliability":"NO_SAMPLE" if not n else "EXPLORATORY_SAME_DAY_NOT_CALIBRATION"}
    if not n:return out
    out["average_home_error_goals_actual_minus_expected"]=round(sum(r["home_goal_error"] for r in rows)/n,5)
    out["average_away_error_goals_actual_minus_expected"]=round(sum(r["away_goal_error"] for r in rows)/n,5)
    out["average_total_error_goals_actual_minus_expected"]=round(sum(r["total_goal_error"] for r in rows)/n,5)
    out["goals_by_market"]={}
    for market in MARKETS:
        measured=[r["probabilities"][market] for r in rows]
        actual=[r["events"][market] for r in rows]
        prior=[r["league_baseline"][market] for r in rows]
        out["goals_by_market"][market]={
         "n":n,
         "predicted_event_rate":round(sum(measured)/n,5),
         "observed_event_rate":round(sum(actual)/n,5),
         "predicted_minus_observed":round((sum(measured)-sum(actual))/n,5),
         "m4_brier":round(sum(score(p,y) for p,y in zip(measured,actual))/n,6),
         "league_pre_nov8_climatology_brier":round(sum(score(p,y) for p,y in zip(prior,actual))/n,6),
         "m4_minus_climatology_brier_lower_is_better":round(
            sum(score(p,y)-score(q,y) for p,q,y in zip(measured,prior,actual))/n,6),
        }
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    r=explain(args.root)
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        require(json.loads(p.read_text(encoding="utf8"))==r,"RESEARCH_REPORT_IMMUTABLE_MISMATCH")
    else:p.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":r["status"],"n":r["scored_m4"],"source":r["source_class_counts"],
          "whole":r["whole"],"strength":r["by_elo_strength"]},
          ensure_ascii=False),flush=True)
if __name__=="__main__":main()
