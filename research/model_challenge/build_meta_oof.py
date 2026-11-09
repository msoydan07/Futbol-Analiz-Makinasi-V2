"""Build historical OOF pair records to train a match-specific M4/XGB gate.

2025/26 OOF construction:
 - XGB fitted strictly on historical fixtures before 2025-07-01.
 - XGB *features* for each target match come from prior dates only.
 - Frozen 2.6.3 M4 fitted per league, per match date, on strictly prior matches.
 - As a bounded diagnostic, only calendar-defined windows are scored:
   day-of-month 01-07 of September/November 2025 and January/March/May 2026.
 - Data not within these windows is still used as earlier history.
 - Targets are 2025/26 only; 2026/27 must not train the gate.
This is RETROSPECTIVE OOF RECONSTRUCTION, not archived sealed forecasts.
"""
from __future__ import annotations
import argparse,csv,json,sys
from collections import defaultdict
from pathlib import Path
from xgb_challenger import make_features,fit,probabilities,LABEL
from next_season_test import PARAMS
from ingest_openfootball import get_json,normalize_one
from m4_xgb_retro_pairs import mk, ROOT

sys.path.insert(0,str(ROOT/"experiments"/"263"))
from m4_integrated import fit_m4,predict_m4,score_markets,use_lock

TRAIN_SPLIT="2025-07-01"
WINDOWS={"2025-09","2025-11","2026-01","2026-03","2026-05"}
MAX_DAY=7
MIN_WARMUP=40

def select(date_string):
    return date_string[:7] in WINDOWS and 1<=int(date_string[8:10])<=MAX_DAY

def build(archive_path,lock_path,out_path):
    with open(archive_path,encoding="utf8",newline="") as f:
        records=list(csv.DictReader(f))
    if not records or any(row["date"]>"2026-11-09" for row in records):
        raise ValueError("bad archive")
    # Not using any 2026/27 results, even for time-lag features.
    records=[row for row in records if row["date"]<"2026-07-01"]
    records.sort(key=lambda r:(r["date"],r["league"],r["home"],r["away"]))
    lock=json.loads(Path(lock_path).read_text(encoding="utf8"))
    settings=use_lock(lock)
    history=[{"league":r["league"],"season":r["season"],
       "match_date":r["date"],"fixture_id":"|".join(mk(r)),
       "home_id":r["home"],"away_id":r["away"],
       "home_goals":int(r["home_goals"]),"away_goals":int(r["away_goals"]),
       "result":("H" if int(r["home_goals"])>int(r["away_goals"]) else
                 "D" if int(r["home_goals"])==int(r["away_goals"]) else "A")}
       for r in records]
    features=make_features(records)
    train=[r for r in features if r[0]["date"]<TRAIN_SPLIT and r[3]>=MIN_WARMUP]
    test=[r for r in features if r[0]["date"]>=TRAIN_SPLIT and
          select(r[0]["date"]) and r[3]>=MIN_WARMUP]
    if len(train)<2000 or len(test)<100:
        raise ValueError("too few OOF training fixtures")
    xgb_model=fit(train,PARAMS)
    xgb_probs=dict(zip((mk(r[0]) for r in test),
                       probabilities(xgb_model,test)))
    targets=defaultdict(list)
    for r in records:
        if r["date"]>=TRAIN_SPLIT and select(r["date"]) and mk(r) in xgb_probs:
            targets[(r["league"],r["date"])].append(r)
    paired=[];unavailable=[]
    for (league,day),batch in sorted(targets.items()):
        m4=fit_m4(history,league,day,settings)
        if m4 is None:
            unavailable.extend({"league":league,"date":day,"reason":"M4_NO_FIT"}
                               for _ in batch)
            continue
        for row in batch:
            k=mk(row)
            lams=predict_m4(m4,row["home"],row["away"])
            if lams is None:
                unavailable.append({"league":league,"date":day,"reason":"M4_NO_LAMBDA"})
                continue
            m4p=score_markets(*lams)["markets"]["1X2"]
            xp=xgb_probs[k]
            xgbp={label:float(xp[LABEL[label]]) for label in ("H","D","A")}
            label="H" if int(row["home_goals"])>int(row["away_goals"]) else (
                "D" if int(row["home_goals"])==int(row["away_goals"]) else "A")
            paired.append({"league":league,"date":day,
                           "home_id":row["home"],"away_id":row["away"],
                           "trained_history_cutoff":TRAIN_SPLIT,
                           "forecast_provenance":"OUT_OF_FOLD_BEFORE_MATCH",
                           "m4":m4p,"xgboost":xgbp,"result":label})
    if len(paired)<100:
        raise ValueError("fewer than 100 causal historical pairs")
    result={
        "schema":"MC_META_GATE_OOF_TRAIN_V1",
        "status":"RETROSPECTIVE_OUT_OF_FOLD_HISTORICAL_RECONSTRUCTION",
        "selection_windows":sorted(WINDOWS),
        "selected_days_per_month":"01-07",
        "xgb_training_period_end_exclusive":TRAIN_SPLIT,
        "M4_original_code_unmodified":True,
        "M4_dev_lock_settings":lock["settings"],
        "gate_training_only":True,
        "gate_evaluation_2026_27_not_used":True,
        "paired_count":len(paired),
        "unavailable_count":len(unavailable),
        "pairs":paired,"failures":unavailable
    }
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                   encoding="utf8")
    print(json.dumps({k:result[k] for k in (
        "schema","paired_count","unavailable_count","status")},indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True)
    p.add_argument("--lock",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    build(a.archive,a.lock,a.out)
