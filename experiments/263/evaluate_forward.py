"""Score only previously registered C3 forward records against NEW final results.

Offline reporting only; never rewrites predictions. Requires identifiable real
match score, kickoff in past, and SHA-256-validated historical JSON payloads.
A passing report is not a model promotion or betting recommendation.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from forward_c3 import SCHEMA, canonical_bytes, read_aware
from exp_263_batch import clean_rows

COLUMNS = ("C0_league_reference", "C1_existing_model_b", "C3_opponent_adjusted")


def collect(prediction_dir, actual_csv, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone_required")
    now = now.astimezone(timezone.utc)
    actuals = clean_rows(actual_csv)
    actual_by_identity = defaultdict(list)
    for r in actuals:
        actual_by_identity[(r["league"], r["home_id"], r["away_id"], r["match_date"])].append(r)
    records = []
    seen_fixtures = set()
    for filename in sorted(Path(prediction_dir).glob("*/*.json")):
        item = json.loads(filename.read_text(encoding="utf-8"))
        if item.get("schema") != SCHEMA:
            raise ValueError(f"Unexpected record schema: {filename}")
        digest = item.pop("payload_sha256", None)
        if not digest or hashlib.sha256(canonical_bytes(item)).hexdigest() != digest:
            raise ValueError(f"Record digest mismatch: {filename}")
        item["payload_sha256"] = digest
        fixture = item["fixture"]
        kickoff = read_aware(fixture["kickoff_utc"])
        created = read_aware(item["created_at_utc"])
        official_checked = read_aware(fixture["source_checked_at_utc"])
        if not official_checked <= created < kickoff:
            raise ValueError(f"Record was not verified and sealed before kickoff: {filename}")
        if fixture.get("fixture_verification") != "VERIFIED_BY_LIVE_OFFICIAL_GATE":
            raise ValueError("No source-verified fixture flag")
        key = (fixture["league"], fixture["home_id"], fixture["away_id"], fixture["match_local_date"])
        if key in seen_fixtures:
            raise ValueError("Duplicate sealed prediction for a single fixture: manual review required")
        seen_fixtures.add(key)
        if kickoff >= now:
            continue
        matches = actual_by_identity.get(key, [])
        if len(matches) > 1:
            raise ValueError(f"Multiple final score rows for {key}")
        if not matches:
            continue
        actual = matches[0]
        event_idx = ("H", "D", "A").index(actual["result"])
        scores = {}
        for name in COLUMNS:
            probs = item["probabilities"].get(name)
            if probs is None:
                continue
            pv = [float(probs[k]) for k in ("H", "D", "A")]
            if not all(math.isfinite(v) and 0 <= v <= 1 for v in pv) or abs(sum(pv)-1)>1e-9:
                raise ValueError("Malformed saved probability vector")
            scores[name] = {
                "logloss": -math.log(max(1e-12, pv[event_idx])),
                "brier": sum((v-int(i==event_idx))**2 for i,v in enumerate(pv))
            }
        records.append({"fixture_key": key, "date":fixture["match_local_date"], "scores":scores, "record_sha256":digest})
    return records, len(seen_fixtures)


def average(records, name):
    rows = [r["scores"][name] for r in records if name in r["scores"]]
    return {"n":len(rows), "logloss":sum(x["logloss"] for x in rows)/len(rows) if rows else None,
            "brier":sum(x["brier"] for x in rows)/len(rows) if rows else None}


def bootstrap_date_ci(paired, n=600):
    if len(paired) < 15:
        return None
    from random import Random
    blocks = defaultdict(list)
    for r in paired:
        block = r["scores"]["C1_existing_model_b"]
        candidate = r["scores"]["C3_opponent_adjusted"]
        blocks[r["date"]].append((block["logloss"]-candidate["logloss"], block["brier"]-candidate["brier"]))
    days = sorted(blocks)
    rng = Random(20261101)
    dist = {"logloss": [], "brier": []}
    for _ in range(n):
        sampled = [blocks[days[rng.randrange(len(days))]] for _ in days]
        points = [p for g in sampled for p in g]
        if not points:
            continue
        for name,i in (("logloss",0),("brier",1)):
            dist[name].append(sum(p[i] for p in points)/len(points))
    return {name: {"lo":sorted(vals)[int(.025*len(vals))], "hi":sorted(vals)[int(.975*len(vals))-1]}
            for name,vals in dist.items()}


def report(prediction_dir, actual_csv, now=None):
    records, total = collect(prediction_dir, actual_csv, now)
    common = [r for r in records if all(k in r["scores"] for k in COLUMNS)]
    by_league = {}
    for league in sorted({r["fixture_key"][0] for r in common}):
        subset=[r for r in common if r["fixture_key"][0]==league]
        by_league[league]={name:average(subset,name) for name in COLUMNS}
    ci=bootstrap_date_ci(common)
    sm={name:average(common,name) for name in COLUMNS}
    n=len(common)
    improvement=(sm["C1_existing_model_b"]["logloss"]-sm["C3_opponent_adjusted"]["logloss"] if n else None)
    brier_improvement=(sm["C1_existing_model_b"]["brier"]-sm["C3_opponent_adjusted"]["brier"] if n else None)
    supported_leagues=sum(all(v[k]["n"]>=15 for k in ("C1_existing_model_b","C3_opponent_adjusted")) for v in by_league.values())
    leagues_better=sum(v["C3_opponent_adjusted"]["logloss"]<v["C1_existing_model_b"]["logloss"]
                      for v in by_league.values() if v["C3_opponent_adjusted"]["n"]>=15)
    day_count=len({r["date"] for r in common})
    # Precommitted practical gate; descriptive, not proof of betting advantage.
    eligible= n>=300 and day_count>=50 and supported_leagues>=8
    meets= (eligible and improvement>=.005 and brier_improvement>=0 and ci is not None
            and ci["logloss"]["lo"]>0 and leagues_better>=7)
    return {
        "schema":"c3_forward_evaluation_v1", "prematch_predictions_seen":total,
        "completed_scores_found":len(records), "paired_all_three":n,
        "days":day_count, "qualified_leagues":supported_leagues,
        "C3_better_leagues_with_n_ge_15":leagues_better,
        "paired_scores":sm, "C1_minus_C3_positive_is_better":{
            "logloss":improvement, "brier":brier_improvement},
        "paired_date_bootstrap_95":ci, "by_league":by_league,
        "outcome":"EVIDENCE_CRITERIA_MET_REQUIRES_ENGINEERING_REVIEW" if meets else "NO_PROMOTION_EVIDENCE_YET",
        "criteria": "300 genuinely forward paired games, 50 different days, >=8 leagues with >=15; C1-C3 logloss >=.005, Brier >=0, date CI lower >0, C3 wins >=7 leagues; manual review always required",
        "limitations": "Pre-registered observational forward comparison; neither betting EV nor full template compliance proven",
        "evaluated_record_hashes":sorted(r["record_sha256"] for r in records),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--records",default="forward_263")
    p.add_argument("--final-scores",required=True)
    p.add_argument("--out",default="forward_263_evaluation.json")
    a=p.parse_args()
    try:
        r=report(a.records,a.final_scores)
        with Path(a.out).open("x",encoding="utf-8") as f:
            json.dump(r,f,ensure_ascii=False,sort_keys=True,indent=2)
            f.write("\n")
        print(json.dumps({k:r[k] for k in ("paired_all_three", "outcome")},ensure_ascii=False))
    except (OSError,KeyError,ValueError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc


if __name__=="__main__":
    main()
