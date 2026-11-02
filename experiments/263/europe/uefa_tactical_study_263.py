"""Historical UEFA league-phase tactical context AB study, experimental only.

PRE-REGISTERED: Train CL+EL 2024/25, hold out entire CL 2025/26. Three
Poisson total-goal comparison specifications; not the four main engines.
Historical public-domain openfootball snapshots are pinned to one commit and
checked against UEFA official competition-level goal counts. Individual
match pages and pre-match rank were NOT independently verified.

The pre-kickoff points/goal difference are reconstructed exclusively from
earlier *matchdays*, never same-day or future results. No UEFA source data are
merged into the 10 domestic leagues or model/ledger.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
import re
import urllib.request
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

import numpy as np

VERSION="263_UEFA_CONTEXT_ABLATION_LOCKED_v1"
SOURCE_COMMIT="abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef"
SOURCES={
    ("UEFA_CL","2024-2025"):("2024-25/cl.txt",144,470),
    ("UEFA_EL","2024-2025"):("2024-25/el.txt",144,408),
    ("UEFA_CL","2025-2026"):("2025-26/cl.txt",144,487),
}
MONTHS={m:i+1 for i,m in enumerate(("Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec"))}
class StudyError(ValueError): pass

def fetch_pinned_source(relative):
    if relative not in {v[0] for v in SOURCES.values()}:
        raise StudyError("UNLISTED_SOURCE")
    url=("https://raw.githubusercontent.com/openfootball/champions-league/"
         +SOURCE_COMMIT+"/"+relative)
    request=urllib.request.Request(url,headers={"User-Agent":"263-uefa-context-audit/1.0"})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(100_000)
    if len(data)>90_000 or len(data)<1_000:
        raise StudyError("SOURCE_BYTES_OUT_OF_BOUNDS")
    return data,url

def parse_league_phase(raw,competition,season):
    lines=raw.decode("utf-8-sig").splitlines()
    season_year=int(season[:4])
    active=False;day=None;matchday=None
    rows=[]
    for rawline in lines:
        s=rawline.strip()
        if s.startswith("▪"):
            active=s.startswith("▪ League")
            matchday=None
            if active:
                v=re.search(r"Matchday (\d+)",s)
                if v:matchday=int(v.group(1))
            continue
        if not active:continue
        dt=re.fullmatch(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) (\d{1,2})(?: (\d{4}))?",s)
        if dt:
            month=MONTHS.get(dt.group(2))
            if month is None:raise StudyError("UNKNOWN_SOURCE_MONTH")
            year=int(dt.group(4)) if dt.group(4) else (season_year if month>=7 else season_year+1)
            day=date(year,month,int(dt.group(3))).isoformat()
            continue
        if " v " not in rawline:continue
        if day is None:raise StudyError("MATCH_WITHOUT_DATE")
        left,right=rawline.split(" v ",1)
        home=re.sub(r"^\s*\d{2}:\d{2}\s+","",left).strip()
        m=re.fullmatch(r"\s*(.*?)\s{2,}(\d{1,2})-(\d{1,2})(?:\s+.*)?",right)
        if m is None:raise StudyError("UNPARSED_LEAGUE_SCORE:"+rawline.strip())
        away=m.group(1).strip();hg=int(m.group(2));ag=int(m.group(3))
        if not home or not away or home==away or hg>40 or ag>40:
            raise StudyError("BAD_FIXTURE_SCORE_OR_TEAM")
        rows.append({"competition":competition,"season":season,"date":day,
                     "matchday":matchday,"home":home,"away":away,"hg":hg,"ag":ag,
                     "total_goals":hg+ag})
    if competition=="UEFA_EL":
        dates=sorted({r["date"] for r in rows})
        day_to_round={};index=0;last=None
        for dayvalue in dates:
            if last is None or (date.fromisoformat(dayvalue)-date.fromisoformat(last)).days>1:
                index+=1
            day_to_round[dayvalue]=index;last=dayvalue
        for r in rows:r["matchday"]=day_to_round[r["date"]]
    return sorted(rows,key=lambda r:(r["matchday"],r["date"],r["home"],r["away"]))

def validate_source_rows(rows,competition,season,expected_n,expected_goals):
    if len(rows)!=expected_n or sum(r["total_goals"] for r in rows)!=expected_goals:
        raise StudyError("SOURCE_VS_OFFICIAL_AGGREGATE_MISMATCH")
    counts=Counter(r["matchday"] for r in rows)
    if counts!={i:18 for i in range(1,9)}:
        raise StudyError("EIGHT_MATCHDAYS_EXPECTED_18_EACH:"+str(counts))
    teams=Counter()
    match_keys=set()
    for row in rows:
        teams.update((row["home"],row["away"]))
        key=(row["home"],row["away"],row["date"])
        if key in match_keys:raise StudyError("DUPLICATED_MATCH_IN_SOURCE")
        match_keys.add(key)
        if row["season"]!=season or row["competition"]!=competition:
            raise StudyError("WRONG_COMPETITION_OR_SEASON")
    if len(teams)!=36 or set(teams.values())!={8}:
        raise StudyError("UEFA_LEAGUE_TEAM_COVERAGE_NOT_36_X_8")
    return {"season":season,"competition":competition,"matches":len(rows),
            "goals":expected_goals,"teams":36,
            "matchdays":dict(sorted(counts.items()))}

def reconstruct_pre_match(rows):
    """No target match OR same-matchday result is visible to any feature."""
    groups=defaultdict(list)
    for r in rows:groups[(r["competition"],r["season"])].append(r)
    result=[]
    for key,group in sorted(groups.items()):
        state=defaultdict(lambda:{"played":0,"pts":0,"gf":0,"ga":0})
        for md in range(1,9):
            block=[r for r in group if r["matchday"]==md]
            if len(block)!=18:raise StudyError("INVALID_MATCHDAY_BLOCK")
            for r in block:
                h=state[r["home"]].copy();a=state[r["away"]].copy()
                if h["played"]!=md-1 or a["played"]!=md-1:
                    raise StudyError("PRE_MATCH_STANDING_NOT_FROM_PREVIOUS_ROUNDS")
                den=max(1,md-1)
                # Constant pseudo-prior 3.0 goals/match, 2 pseudo-games.
                # Only prior UEFA match scores enter; no future statistics.
                prev_combined=(h["gf"]+h["ga"]+a["gf"]+a["ga"]+6)/(2*(md-1)+2)
                x={**r,"before_home_points":h["pts"],"before_away_points":a["pts"],
                   "before_home_games":h["played"],"before_away_games":a["played"],
                   "before_home_goal_difference":h["gf"]-h["ga"],
                   "before_away_goal_difference":a["gf"]-a["ga"],
                   "ppg_gap_abs":abs(h["pts"]/den-a["pts"]/den),
                   "gd_per_game_gap_abs":abs((h["gf"]-h["ga"])/den-(a["gf"]-a["ga"])/den),
                   "both_teams_prior_total_goals":prev_combined,
                   "less_successful_team_ppg":min(h["pts"],a["pts"])/den,
                   "late_md":int(md>=6)}
                result.append(x)
            # Update all standings AFTER features for the matchday are made.
            for r in block:
                h=state[r["home"]];a=state[r["away"]]
                gh=r["hg"];ga=r["ag"]
                h["played"]+=1;a["played"]+=1
                h["gf"]+=gh;h["ga"]+=ga
                a["gf"]+=ga;a["ga"]+=gh
                h["pts"]+=3 if gh>ga else 1 if gh==ga else 0
                a["pts"]+=3 if ga>gh else 1 if ga==gh else 0
        if len({r["home"] for r in group}|{r["away"] for r in group})!=36:
            raise StudyError("TEAM_UNIVERSE_CHANGED")
    return result

# The designs and penalties are fixed BEFORE evaluation. No hyperparam search.
DESIGNS={
    "BASE_COMPETITION_ONLY":("intercept","is_europa"),
    "STRENGTH_PROXY":("intercept","is_europa","prior_goals_minus3",
                      "ppg_gap_abs","gd_per_game_gap_abs"),
    "STRENGTH_PLUS_POINTS_PHASE":("intercept","is_europa","prior_goals_minus3",
                      "ppg_gap_abs","gd_per_game_gap_abs","late_md",
                      "late_ppg_gap","late_lower_ppg","matchday_fraction"),
}
def features(r):
    return {
        "intercept":1.,
        "is_europa":float(r["competition"]=="UEFA_EL"),
        "prior_goals_minus3":r["both_teams_prior_total_goals"]-3.,
        "ppg_gap_abs":r["ppg_gap_abs"],
        "gd_per_game_gap_abs":r["gd_per_game_gap_abs"],
        "late_md":float(r["late_md"]),
        "late_ppg_gap":r["late_md"]*r["ppg_gap_abs"],
        "late_lower_ppg":r["late_md"]*r["less_successful_team_ppg"],
        "matchday_fraction":(r["matchday"]-1)/7.,
    }

def fit(train,design):
    cols=DESIGNS[design]
    x=np.asarray([[features(r)[c] for c in cols] for r in train],float)
    y=np.asarray([r["total_goals"] for r in train],float)
    if not len(y):raise StudyError("EMPTY_TRAIN")
    penalties=np.asarray([0 if c=="intercept" else 5 if c=="is_europa" else 15
                          for c in cols],float)
    theta=np.zeros(len(cols))
    theta[0]=math.log(float(np.mean(y)))
    for _ in range(100):
        mu=np.exp(np.clip(x@theta,-3,3))
        gradient=x.T@(mu-y)+penalties*theta
        hessian=x.T@(x*mu[:,None])+np.diag(penalties)
        correction=np.linalg.solve(hessian,gradient)
        theta-=correction
        if max(abs(correction))<1e-9:break
    if not np.isfinite(theta).all():raise StudyError("BAD_FIT")
    return {"design":design,"cols":cols,"coefficients":theta.tolist()}

def predict(r,fit_result):
    v=sum(features(r)[c]*b for c,b in zip(fit_result["cols"],fit_result["coefficients"]))
    return math.exp(max(-3,min(3,v)))

def loss_one(mu,y):
    return mu-y*math.log(mu)+math.lgamma(y+1)

def p_over25(mu):
    return 1-math.exp(-mu)*(1+mu+mu*mu/2)

def metrics(rows,preds):
    if len(rows)!=len(preds) or not rows:raise StudyError("INVALID_METRICS")
    n=len(rows)
    return {
        "n":n,
        "mean_poisson_log_loss":sum(loss_one(p,r["total_goals"]) for r,p in zip(rows,preds))/n,
        "over25_brier":sum((p_over25(p)-int(r["total_goals"]>2))**2
                           for r,p in zip(rows,preds))/n,
        "goals_mae":sum(abs(p-r["total_goals"]) for r,p in zip(rows,preds))/n,
        "average_predicted_goals":sum(preds)/n,
        "average_actual_goals":sum(r["total_goals"] for r in rows)/n}

def by_phase(rows):
    out={}
    for comp,season in sorted({(r["competition"],r["season"]) for r in rows}):
        rr=[r for r in rows if (r["competition"],r["season"])==(comp,season)]
        for label,mds in (("MD1_4",set(range(1,5))),("MD5_8",set(range(5,9)))):
            group=[r for r in rr if r["matchday"] in mds]
            out[comp+"_"+season+"_"+label]={
                "n":len(group),"goals_per_match":sum(r["total_goals"] for r in group)/len(group),
                "over25_rate":sum(r["total_goals"]>2 for r in group)/len(group)}
    return out

def blocked_bootstrap(rows,baseline,variant,iterations=1200):
    """Descriptive uncertainty via eight 18-match UEFA matchday blocks."""
    blocks=defaultdict(list)
    for index,r in enumerate(rows):blocks[r["matchday"]].append(index)
    if sorted(blocks)!=list(range(1,9)):
        raise StudyError("BOOTSTRAP_ROUND_COVERAGE")
    random_state=random.Random(263)
    round_ids=sorted(blocks)
    observed=[loss_one(q,r["total_goals"])-loss_one(p,r["total_goals"])
              for r,p,q in zip(rows,baseline,variant)]
    deltas=[]
    for _ in range(iterations):
        indexes=[i for md in [random_state.choice(round_ids) for _ in round_ids]
                 for i in blocks[md]]
        deltas.append(sum(observed[i] for i in indexes)/len(indexes))
    deltas.sort()
    return {"mean_variant_minus_baseline":sum(observed)/len(observed),
            "block_bootstrap_95pct":[deltas[int(.025*(iterations-1))],
                                     deltas[int(.975*(iterations-1))]],
            "blocks":8,"iterations":iterations,
            "interval_is_not_independent_season_replication":True}

def run_corpus(texts):
    source_audit=[]
    rows=[]
    for (comp,season),(relative,n,g) in SOURCES.items():
        raw=texts.get(relative)
        if not isinstance(raw,bytes):raise StudyError("MISSING_PINNED_CORPUS_SOURCE")
        parsed=parse_league_phase(raw,comp,season)
        audit=validate_source_rows(parsed,comp,season,n,g)
        audit.update({"file":relative,"source_sha256":hashlib.sha256(raw).hexdigest()})
        source_audit.append(audit)
        rows+=parsed
    enriched=reconstruct_pre_match(rows)
    train=[r for r in enriched if r["season"]=="2024-2025"]
    holdout=[r for r in enriched if r["season"]=="2025-2026" and r["competition"]=="UEFA_CL"]
    if len(train)!=288 or len(holdout)!=144:
        raise StudyError("FROZEN_TRAIN_HOLDOUT_COUNTS_CHANGED")
    fitted={name:fit(train,name) for name in DESIGNS}
    predictions={name:[predict(r,parameters) for r in holdout]
                 for name,parameters in fitted.items()}
    scores={name:metrics(holdout,pred) for name,pred in predictions.items()}
    baseline=predictions["BASE_COMPETITION_ONLY"]
    diffs={name:blocked_bootstrap(holdout,baseline,predictions[name])
           for name in ("STRENGTH_PROXY","STRENGTH_PLUS_POINTS_PHASE")}
    return {
        "schema":VERSION,
        "status":"HISTORICAL_EXPERIMENT_NO_PROMOTION",
        "source":{"repository":"openfootball/champions-league",
                  "commit":SOURCE_COMMIT,
                  "official_aggregate_parity_only":True,
                  "official_uefa_match_by_match_checked":False,
                  "audits":source_audit},
        "design":{"development":"2024/25 CL and EL (288)","sealed_out_of_season_test":"2025/26 CL (144)",
                  "no_2025_26_europa_league_holdout":True,
                  "feature_cutoff":"previous MATCHDAY only; never same matchday or later",
                  "no_real_domestic_crosswalk_or_opponent_interleague_rating":True,
                  "strength_features_are_UEFA_prior_matchday_proxies":True,
                  "missing_team_prior_uses_fixed_prior_3goals":True,
                  "point_pressure_is_a_proxy_not_ground_truth_motivation":True,
                  "no_hyperparameter_search_on_holdout":True},
        "descriptive":by_phase(enriched),
        "holdout_metrics":scores,
        "holdout_logscore_uncertainty":diffs,
        "fitted_training_coefficients_only":fitted,
        "decision":{"europe_UEFA_hypothesis_benefit_proven":False,
                    "automatic_goal_rate_multiplier":None,
                    "B_C2_C3_M4_changed":False,
                    "C2_replaced":False,
                    "ABC_approved":False,"pilot_registered":False,
                    "ten_domestic_leagues_modified":False,
                    "needs_more_seasons_independent_source_checks_and_competition_specific_holdouts":True}}

def main(argv=None):
    p=argparse.ArgumentParser(description="Pinned 432-game UEFA league-phase context experiment")
    p.add_argument("--sources-dir",type=Path,help="Offline three source files under 2024-25 and 2025-26")
    p.add_argument("--out",type=Path,default=Path("data/europe_staged_263/uefa_context_ablation_263.json"))
    args=p.parse_args(argv)
    texts={}
    for relative,*_ in SOURCES.values():
        if args.sources_dir:
            data=(args.sources_dir/relative).read_bytes()
        else:
            data,_=fetch_pinned_source(relative)
        texts[relative]=data
    result=run_corpus(texts)
    if Path("data/europe_staged_263") not in args.out.parents or args.out.suffix!=".json":
        raise StudyError("OUTPUT_MUST_BE_EUROPE_QUARANTINE_JSON")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                        encoding="utf-8")
    print("UEFA_CONTEXT_STUDY_RESULT="+json.dumps({
        "status":result["status"],
        "source_matches":[(x["competition"],x["season"],x["matches"],x["goals"])
                          for x in result["source"]["audits"]],
        "early_late":result["descriptive"],
        "holdout_metrics":result["holdout_metrics"],
        "uncertainty":result["holdout_logscore_uncertainty"],
        "automatic_goal_modifier":None,
        "models_promoted":[],"pilot_registered":False},sort_keys=True))
if __name__=="__main__":
    main()
