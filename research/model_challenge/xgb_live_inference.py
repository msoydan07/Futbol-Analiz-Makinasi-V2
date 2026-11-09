"""XGBoost V1 -- strictly pre-kickoff training/inference for MS 1-X-2.

Two inputs only:
  1. Played-results CSV supplied from a source verified independently.
  2. Future fixture evidence JSON supplied by an independent official gate.

This NEVER discovers/verifies fixtures on its own. A URL is NOT evidence
of verification by itself; caller is responsible for the actual official
fixture lookup and for validating source rights and completeness.

The model uses only results strictly before the forecast date, and the
*same feature formula* as historical xgb_challenger.make_features. Research
output can be passed to prospective_seal; other experts are explicitly PAS.

Usage:
 python research/model_challenge/xgb_live_inference.py \
   --history results.csv --fixture official_verified_fixture.json \
   --out /tmp/xgb_live_candidate.json

The --as-of timestamp is taken from the verified fixture manifest and MUST
be recent. This process never makes up an official source or match.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import numpy as np

from xgb_challenger import Team,make_features,fit,LABEL
from next_season_test import PARAMS
from prospective_seal import dt,validate,Rejected,KNOWN_LEAGUES

REQUIRED_FIELDS=("league","date","home","away","home_goals","away_goals")
VERSION="XGBOOST_V1_RESULTS_ONLY_263_RESEARCH"
TRAIN_WARMUP=40
MIN_TRAIN=1000
MIN_LEAGUE_MATCHES=40
MAX_SOURCE_STALENESS_DAYS=21
MAX_FEATURES=25

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load_history(path,cutoff):
    raw=Path(path).read_bytes()
    text=raw.decode("utf-8")
    rows=list(csv.DictReader(text.splitlines()))
    if not rows or not set(REQUIRED_FIELDS).issubset(rows[0]):
        raise ValueError("history columns missing")
    seen=set()
    for row in rows:
        if not all(row.get(k) for k in REQUIRED_FIELDS):
            raise ValueError("history has missing fields")
        day=date.fromisoformat(row["date"])
        if day>=cutoff:
            raise ValueError("history contains fixture date or later; fail closed")
        if row["home"]==row["away"]:
            raise ValueError("self match")
        k=tuple(row[x] for x in ("league","date","home","away"))
        if k in seen:raise ValueError("duplicated fixture")
        seen.add(k)
        for fld in ("home_goals","away_goals"):
            number=int(row[fld])
            if str(number)!=row[fld] or not 0<=number<=30:
                raise ValueError("invalid goals")
    rows.sort(key=lambda r:(r["date"],r["league"],r["home"],r["away"]))
    return rows,sha(raw)

def club_id(name):
    return "club-"+hashlib.sha256(name.encode("utf8")).hexdigest()[:24]

def feature_at(rows,league,home,away,fixture_date):
    """Exactly the historical feature contract, without any fake score."""
    lid={name:i for i,name in enumerate(sorted({r["league"] for r in rows}))}
    if league not in lid:
        raise ValueError("unknown league in fitted feature encoder")
    teams=defaultdict(Team)
    leagues=defaultdict(lambda:[0,0,0,0])
    for r in rows:
        if r["date"]>=fixture_date.isoformat():
            raise ValueError("same-day result in forecast history")
        k=r["league"];now=date.fromisoformat(r["date"])
        h,a=int(r["home_goals"]),int(r["away_goals"])
        teams[k,r["home"]].add(now,"H",h,a)
        teams[k,r["away"]].add(now,"A",a,h)
        s=leagues[k];s[0]+=1;s[1]+=h;s[2]+=a;s[3]+=int(h==a)
    h=teams[league,home];a=teams[league,away]
    if h.games<3 or a.games<3:
        raise ValueError("team not sufficiently mapped to historical identity")
    n,hg,ag,draw=leagues[league]
    if n<MIN_LEAGUE_MATCHES:
        raise ValueError("league warmup not met")
    h5,h10,a5,a10=h.stats(5),h.stats(10),a.stats(5),a.stats(10)
    hr,ar=h.rest(fixture_date),a.rest(fixture_date)
    feats=[lid[league],h.games,a.games,*h5,*a5,*h10,*a10,
       h.venue_pts("H"),a.venue_pts("A"),hr,ar,hr-ar,
       (h.points+5.2)/(h.games+4),(a.points+5.2)/(a.games+4),
       (hg+1.45*35)/(n+35),(ag+1.15*35)/(n+35),
       (draw+.265*35)/(n+35)]
    return np.asarray(feats,dtype=np.float32),{"games_home":h.games,
        "games_away":a.games,"league_matches":n}

def inference(history_path,manifest_path,now=None):
    now=now or datetime.now(timezone.utc)
    now=dt(now.isoformat())
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf8"))
    allowed={"schema","fixture_id","league","home_name","away_name",
             "home_id","away_id",
             "kickoff_utc","official_fixture_url","source_verified_at_utc",
             "history_asof_utc","fixture_verified_by"}
    if set(manifest)!=allowed or manifest["schema"]!="MC_VERIFIED_FIXTURE_INPUT_V1":
        raise ValueError("invalid fixture manifest")
    if manifest["fixture_verified_by"]!="EXTERNAL_OFFICIAL_GATE":
        raise ValueError("unverified fixture; URL alone is insufficient")
    if manifest["league"] not in KNOWN_LEAGUES:
        raise ValueError("out-of-scope league")
    created=now
    kickoff=dt(manifest["kickoff_utc"])
    checked=dt(manifest["source_verified_at_utc"])
    history_asof=dt(manifest["history_asof_utc"])
    if not (history_asof<=checked<=created<kickoff):
        raise ValueError("invalid source timing")
    if created-checked>timedelta(hours=12) or kickoff-created<timedelta(minutes=2):
        raise ValueError("stale fixture evidence or kickoff too close")
    day=kickoff.date()
    if any(not isinstance(manifest[k],str) or not manifest[k].strip() for k in ("home_name","away_name","home_id","away_id")):
        raise ValueError("missing verified team identities")
    if manifest["home_name"]==manifest["away_name"] or manifest["home_id"]==manifest["away_id"]:
        raise ValueError("invalid fixture participants")
    # UTC date is deliberately conservative for matches around midnight.
    # Production should use a fully source-verified local match date.
    if kickoff.hour<3:
        raise ValueError("UTC-midnight fixture requires verified local-date mapping")
    if day-date.fromisoformat(history_asof.date().isoformat())>timedelta(days=MAX_SOURCE_STALENESS_DAYS+1):
        raise ValueError("history as-of too stale")
    rows,hsha=load_history(history_path,day)
    if not rows:
        raise ValueError("empty historical archive")
    if any(date.fromisoformat(r["date"])>=history_asof.date() for r in rows):
        raise ValueError("played results are later than verified history cutoff")
    # The source must have current league results, not merely a recent manifest date.
    league_dates=[date.fromisoformat(r["date"]) for r in rows
                  if r["league"]==manifest["league"]]
    if not league_dates or (day-max(league_dates)).days>MAX_SOURCE_STALENESS_DAYS:
        raise ValueError("stale league result coverage")
    train=[r for r in make_features(rows) if r[3]>=TRAIN_WARMUP]
    if len(train)<MIN_TRAIN:
        raise ValueError("insufficient model training matches")
    x,detail=feature_at(rows,manifest["league"],manifest["home_name"],
                        manifest["away_name"],day)
    if x.shape!=(MAX_FEATURES,) or not np.isfinite(x).all():
        raise ValueError("feature shape/finiteness mismatch")
    model=fit(train,PARAMS)
    p=model.predict_proba(x.reshape(1,-1))[0]
    p=np.asarray(p,dtype=float);p=p/p.sum()
    if not np.isfinite(p).all() or not np.all((p>0)&(p<1)):
        raise ValueError("invalid XGBoost output")
    probabilities={k:float(p[i]) for k,i in LABEL.items()}
    parts=[Path(__file__),Path(__file__).with_name("xgb_challenger.py"),
           Path(__file__).with_name("next_season_test.py")]
    this_code=sha(b"".join(part.read_bytes() for part in parts))
    models={key:{"status":"PAS","probabilities":None} for key in
            ("Elo","Poisson","XGBoost","EqualWeightHybrid")}
    models["XGBoost"]={"status":"AVAILABLE","probabilities":probabilities}
    from prospective_seal import digest
    source={"official_fixture_url":manifest["official_fixture_url"],
      "source_verified_at_utc":manifest["source_verified_at_utc"],
      "history_asof_utc":manifest["history_asof_utc"],
      "model_code_sha":this_code,
      "history_sha":hsha}
    candidate={"schema":"MC_PROSPECTIVE_SHADOW_INPUT_V1",
      "fixture":{"fixture_id":manifest["fixture_id"],"league":manifest["league"],
                 "home_id":manifest["home_id"],
                 "away_id":manifest["away_id"],
                 "kickoff_utc":manifest["kickoff_utc"]},
      "source":source,"models":models,"created_at_utc":now.isoformat()}
    validate(candidate,now)
    return candidate,{"model":VERSION,"features":int(x.shape[0]),
        "training_matches":len(train),"input_team_games":detail,
        "output":"RESEARCH_ONLY_NOT_263_PROMOTED",
        "source_verified_externally_not_by_this_script":True,
        "betting_authorized":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",required=True)
    parser.add_argument("--fixture",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--seal-root",required=True,
        help="Research-only immutable SHA seal location")
    a=parser.parse_args()
    candidate,info=inference(a.history,a.fixture)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf8") as f:
        f.write(json.dumps(candidate,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    from prospective_seal import seal
    sealed_path,locked_sha=seal(candidate,a.seal_root)
    print(json.dumps({"result":"RESEARCH_ONLY_PREDICTION_SHA_SEALED",
                      "candidate_path":str(out),"sealed_path":str(sealed_path),
                      "payload_sha256":locked_sha,"info":info},ensure_ascii=False))

if __name__=="__main__":main()
