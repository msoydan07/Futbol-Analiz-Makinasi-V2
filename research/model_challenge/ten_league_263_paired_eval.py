"""Ten-league canonical-id research cohort: locked M4 vs frozen XGBoost.

Predeclared evaluation: for each league and ISO calendar week in 2026/27,
the *earliest actual match date of the week*, all matches on that date.
This limits expensive M4 re-fits without adapting to outcomes and preserves
strict same-day temporal cutoffs. Training: 2025/26 ONLY; XGBoost feature
history may use strictly earlier 2026/27 results, not model fitting labels.
No retrospective result may enter same-date features or M4 fit.

WARNING: Prior 2026/27 results have already been inspected in other
research reports; this is exploratory, not unseen validation. Data is
owner-accepted for research, not independently verified match by match.
"""
from __future__ import annotations
import argparse,csv,json,math,sys,random
from collections import defaultdict
from datetime import date
from pathlib import Path

from xgb_challenger import make_features,fit,probabilities,LABEL
from next_season_test import PARAMS

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

CUTOFF="2026-07-01"
LABELS=("H","D","A")

def key(row):
    return (row["league"],row["date"],row["home"],row["away"])

def losses(p,y):
    return (-math.log(max(1e-12,p[y])),
            sum((float(p[z])-int(z==y))**2 for z in LABELS),
            int(max(LABELS,key=lambda z:p[z])==y))

def audit(source,lock_path,out_path):
    with open(source,encoding="utf8",newline="") as fh:
        allrows=list(csv.DictReader(fh))
    if len(allrows)!=4518:
        raise ValueError("expected SHA-controlled owner accepted 4518-row dataset")
    if len({key(r) for r in allrows})!=len(allrows):
        raise ValueError("duplicate fixture")
    allrows.sort(key=lambda r:(r["date"],*key(r)))
    train_rows=[r for r in make_features(allrows)
                if r[0]["date"]<CUTOFF and r[3]>=40]
    if len(train_rows)<1500:
        raise ValueError("insufficient independent prior-season training")
    model=fit(train_rows,PARAMS)
    hist=[{"league":r["league"],"season":r["season"],
           "match_date":r["date"],"fixture_id":"|".join(key(r)),
           "home_id":r["home"],"away_id":r["away"],
           "home_goals":int(r["home_goals"]),
           "away_goals":int(r["away_goals"]),
           "result":("H" if int(r["home_goals"])>int(r["away_goals"]) else
                     "A" if int(r["home_goals"])<int(r["away_goals"]) else "D")}
          for r in allrows]
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    st=use_lock(lock)

    # Before inspecting any outcomes, choose solely by league/week/date.
    chosen_date={}
    for r in allrows:
        if r["date"]<CUTOFF:continue
        d=date.fromisoformat(r["date"])
        iso=d.isocalendar()
        bucket=(r["league"],iso.year,iso.week)
        if bucket not in chosen_date or r["date"]<chosen_date[bucket]:
            chosen_date[bucket]=r["date"]
    selected={key(r) for r in allrows
              if r["date"]>=CUTOFF and r["date"]==chosen_date[
                  (r["league"],date.fromisoformat(r["date"]).isocalendar().year,
                   date.fromisoformat(r["date"]).isocalendar().week)]}
    xrows=[r for r in make_features(allrows)
           if key(r[0]) in selected and r[3]>=40]
    xp=dict(zip((key(r[0]) for r in xrows),probabilities(model,xrows)))
    grouped=defaultdict(list)
    for r in allrows:
        if key(r) in selected:grouped[(r["league"],r["date"])].append(r)
    evaluated=[];failed=[]
    for (league,day),batch in sorted(grouped.items()):
        frozen=fit_m4(hist,league,day,st)
        for r in batch:
            k=key(r)
            lam=predict_m4(frozen,r["home"],r["away"]) if frozen else None
            if lam is None or k not in xp:
                failed.append({"league":league,"date":day,
                               "why":"M4" if lam is None else "XGB"})
                continue
            mp=score_markets(*lam)["markets"]["1X2"]
            xx=xp[k]
            xgp={label:float(xx[LABEL[label]]) for label in LABELS}
            half={label:(mp[label]+xgp[label])/2 for label in LABELS}
            y=hist[allrows.index(r)]["result"]  # label from scored file AFTER inference
            result={"league":league,"date":day,"key":list(k),"result":y}
            for name,p in (("M4",mp),("XGBoost",xgp),("Fixed50",half)):
                ll,bs,acc=losses(p,y)
                result[name+"_logloss"]=ll
                result[name+"_brier"]=bs
                result[name+"_accuracy"]=acc
            evaluated.append(result)
    if len(evaluated)<100:
        raise ValueError("insufficient paired earliest-weekly-day evaluation")
    def summarize(items):
        return {m:{metric:sum(x[m+"_"+metric] for x in items)/len(items)
                   for metric in ("logloss","brier","accuracy")}
                for m in ("M4","XGBoost","Fixed50")}
    league_rows=defaultdict(list)
    byday=defaultdict(list)
    for r in evaluated:
        league_rows[r["league"]].append(r)
        byday[r["date"]].append(r)
    days=sorted(byday)
    rng=random.Random(263)
    bootstrap=[]
    for _ in range(1500):
        chosen=[byday[days[rng.randrange(len(days))]] for _ in days]
        batch=[row for q in chosen for row in q]
        bootstrap.append(sum(r["XGBoost_logloss"]-r["M4_logloss"] for r in batch)/len(batch))
    bootstrap.sort()
    report={"schema":"MC_263_CANONICAL_TEN_LEAGUE_PAIRED_V1",
      "status":"RETROSPECTIVE_ALREADY_INSPECTED_RESEARCH_ONLY",
      "training_before":"2026-07-01",
      "fixed_window_rule":"First actual match date within each league ISO-week; whole date",
      "same_date_outcomes_used_for_training":False,
      "frozen_m4_settings":lock["settings"],
      "xgb_fixed_hyperparameters":PARAMS,
      "training_examples":len(train_rows),
      "target_fixtures":len(selected),
      "paired":len(evaluated),"failed_to_pair":len(failed),
      "overall":summarize(evaluated),
      "per_league":{league:{"n":len(items),"models":summarize(items)}
                    for league,items in sorted(league_rows.items())},
      "xgb_minus_m4_95pct_date_bootstrap":
       [bootstrap[int(.025*(len(bootstrap)-1))],
        bootstrap[int(.975*(len(bootstrap)-1))]],
      "owner_accepted_archive_not_independently_verified":True,
      "not_same_as_original_sealed_263_forecasts":True,
      "original_263_unchanged":True,
      "production_promotion":False,"betting_authorized":False}
    dest=Path(out_path);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({x:report[x] for x in ("paired","failed_to_pair",
        "training_examples","overall","xgb_minus_m4_95pct_date_bootstrap")},indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--lock",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args();audit(a.source,a.lock,a.out)
