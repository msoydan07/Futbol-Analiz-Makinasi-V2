"""Independent skeptical check of 2.6.3 stored Nov-08 research-only forecasts.

Checks forecast-source integrity, coherent probabilities, coverage and
65%-75% empirical calibration of each SEPARATE market. No forecasts refit,
no seals/official results edited, no odds, no promoted model. Post-match
web-reviewed results are NOT an authoritative result-provider attestation.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

DAY="2026-11-08"
SOURCES=("new100_42469245388.json","new100_42469487639.json")
MODELS=("B","C2","C3","M4")
MS=("H","D","A")
LINES=("OVER_1.5","OVER_2.5","OVER_3.5")
EVENTS=("MS_TOP1","MS1","MSX","MS2","KG_VAR",*LINES)
GROUPS=("ALL_WEB_REVIEW","PRIMARY_ONLY")
SCHEMA="263_SECOND_ENGINEER_70_PERCENT_SKEPTICAL_AUDIT_V1"

class EvidenceBlocked(ValueError):pass

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def hash_payload(data):
    clean={k:v for k,v in data.items() if k!="payload_sha256"}
    return hashlib.sha256(json.dumps(clean,sort_keys=True,ensure_ascii=False,
                   separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()

def utc(v):
    if not isinstance(v,str):raise EvidenceBlocked("NAIVE_OR_MISSING_TIME")
    try:d=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError as e:raise EvidenceBlocked("INVALID_TIME") from e
    if d.tzinfo is None:raise EvidenceBlocked("NAIVE_TIME")
    return d.astimezone(timezone.utc)

def probability(p):
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1:
        raise EvidenceBlocked("INVALID_FINITE_PROBABILITY")
    return float(p)

def coherent(m):
    """Score distribution can imply only jointly consistent events."""
    if not isinstance(m,dict) or not isinstance(m.get("1X2"),dict):
        raise EvidenceBlocked("MISSING_1X2")
    v={k:probability(m["1X2"].get(k)) for k in MS}
    if abs(sum(v.values())-1)>1e-7:
        raise EvidenceBlocked("MS_PROBABILITIES_DO_NOT_SUM_TO_1")
    yes=probability(m.get("BTTS_YES"))
    no=probability(m.get("BTTS_NO"))
    if abs(yes+no-1)>1e-7:
        raise EvidenceBlocked("BTTS_COMPLEMENT_MISMATCH")
    o=[probability(m.get(k)) for k in LINES]
    if not o[0]+1e-9>=o[1]>=o[2]-1e-9:
        raise EvidenceBlocked("GOAL_TAIL_MONOTONICITY_BROKEN")
    if yes>o[0]+1e-9:
        raise EvidenceBlocked("BOTH_SCORE_CANNOT_EXCEED_TWO_PLUS_TOTAL")
    for k,p in zip(LINES,o):
        u=probability(m.get(k.replace("OVER","UNDER")))
        if abs(p+u-1)>1e-7:raise EvidenceBlocked("GOAL_LINE_COMPLEMENT_MISMATCH")
    if "MS1" in m and abs(probability(m["MS1"])-v["H"])>1e-7:
        raise EvidenceBlocked("MS1_ALIAS_MISMATCH")
    if "MSX" in m and abs(probability(m["MSX"])-v["D"])>1e-7:
        raise EvidenceBlocked("MSX_ALIAS_MISMATCH")
    if "MS2" in m and abs(probability(m["MS2"])-v["A"])>1e-7:
        raise EvidenceBlocked("MS2_ALIAS_MISMATCH")
    return v

def wilson(success,total,z=1.959963984540054):
    """Wilson 95% binomial interval; not a proof of independence."""
    if type(success)!=int or type(total)!=int or not 0<=success<=total:
        raise EvidenceBlocked("IMPOSSIBLE_BINOMIAL_COUNTS")
    if total==0:return None
    p=success/total;z2=z*z;den=1+z2/total
    centre=(p+z2/(2*total))/den
    half=z*math.sqrt(p*(1-p)/total+z2/(4*total*total))/den
    return [round(max(0,centre-half),4),round(min(1,centre+half),4)]

def band(rows,lower=.65,upper=.75):
    hit=[r for r in rows if lower<=r["p"]<upper]
    n=len(hit)
    days=len({r["match_day"] for r in hit})
    observed=sum(r["y"] for r in hit)
    status=("NO_70_PERCENT_SAMPLES" if n==0 else
            "DESCRIPTIVE_ONLY_TOO_FEW_OR_SAME_DAY" if n<100 or days<5 else
            "SAMPLE_ELIGIBLE_FOR_INDEPENDENT_CONFIRMATION_NOT_PROOF")
    return {"range_inclusive_lower_exclusive_upper":[lower,upper],
        "sample_n":n,"distinct_utc_match_days":days,
        "predicted_mean":round(sum(r["p"] for r in hit)/n,4) if n else None,
        "observed_rate":round(observed/n,4) if n else None,
        "95pct_wilson_independent_binomial_reference_only":wilson(observed,n),
        "calibration_gap_observed_minus_predicted":round(
            observed/n-sum(r["p"] for r in hit)/n,4) if n else None,
        "evidence_status":status,
        "note":"Same-day matches share shocks; naive Wilson interval may understate uncertainty. Historical results already viewed."}

def summary(rows):
    n=len(rows)
    if not n:return {"n":0,"brier":None,"mean_forecast":None,"observed":None,
                     "confidence_65_75":band(rows)}
    return {"n":n,"brier":round(sum((r["p"]-r["y"])**2 for r in rows)/n,6),
        "mean_forecast":round(sum(r["p"] for r in rows)/n,4),
        "observed":round(sum(r["y"] for r in rows)/n,4),
        "confidence_65_75":band(rows)}

def collect(root):
    root=Path(root)
    base=root/"experiments/263"
    overlay=read(base/"nov8_webreview_results_263.json")
    if (overlay.get("schema")!="263_NOV8_WEB_REVIEW_RESEARCH_ONLY_V1" or
        overlay.get("day_turkey")!=DAY or overlay.get("new100_accepted_results")!=0):
        raise EvidenceBlocked("NOT_RESEARCH_OVERLAY")
    outcomes={}
    for r in overlay["rows"]:
        key=(r["league"],r["home"],r["away"])
        if key in outcomes:raise EvidenceBlocked("DUPLICATE_RESULT_NAME_KEY")
        if r.get("source_class") not in (
            "PRIMARY_LEAGUE_OR_CLUB","MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL"):
            raise EvidenceBlocked("UNVERIFIED_RESULT_SOURCE_CLASS")
        if not str(r.get("source_url","")).startswith("https://"):
            raise EvidenceBlocked("MISSING_WEB_REVIEW_SOURCE")
        if r["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL" and not str(r.get("crosscheck_url","")).startswith("https://"):
            raise EvidenceBlocked("MEDIA_SCORE_NOT_CROSSCHECKED")
        if r["status"]=="FULL_TIME":
            if any(type(r.get(x)) is not int or not 0<=r[x]<=20 for x in ("home_goals","away_goals")):
                raise EvidenceBlocked("INVALID_MATCH_RESULT")
        elif r["status"]=="POSTPONED":
            if r["home_goals"] is not None or r["away_goals"] is not None:
                raise EvidenceBlocked("POSTPONED_GAME_HAS_SCORE")
        else:raise EvidenceBlocked("UNEXPECTED_RESULT_STATUS")
        outcomes[key]=r
    sealed={}
    for fname in SOURCES:
        batch=read(base/"sabah_batch_reports"/fname)
        if batch.get("cohort")!="new100" or batch.get("day_turkey")!=DAY or batch.get("schema")!="SABAH_TOPLU_KAYIT_V1":
            raise EvidenceBlocked("WRONG_BATCH_OR_DATE")
        for r in batch["outcomes"]:
            if r.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            key=(r["league"],r["home"],r["away"])
            if key in sealed:raise EvidenceBlocked("DUPLICATE_FORECAST_BETWEEN_BATCHES")
            rel=r["forecast_path"]
            if not re.fullmatch(r"forward_morning_263/2026-11-08/[a-f0-9]{24}\.json",rel):
                raise EvidenceBlocked("UNTRUSTED_SEAL_PATH")
            payload=read(root/rel)
            if hash_payload(payload)!=payload.get("payload_sha256") or payload["payload_sha256"]!=r["forecast_sha256"]:
                raise EvidenceBlocked("FORECAST_OR_BATCH_SHA_MISMATCH")
            fx=payload["fixture"]
            if (fx["league"]!=r["league"] or
                fx["kickoff_utc"]!=r["kickoff_utc"] or
                fx["match_local_date"]!=DAY or
                fx.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"):
                raise EvidenceBlocked("FIXTURE_MISMATCH")
            checked=utc(fx["source_checked_at_utc"])
            created=utc(payload["created_at_utc"])
            kickoff=utc(fx["kickoff_utc"])
            if not (created<kickoff and checked<kickoff and checked<=created+timedelta(seconds=60)):
                raise EvidenceBlocked("NOT_GENUINELY_PREMATCH_TIME")
            if not fx.get("home_id") or not fx.get("away_id") or fx["home_id"]==fx["away_id"]:
                raise EvidenceBlocked("MISSING_CANONICAL_TEAM_IDS_IN_FORECAST")
            sealed[key]=payload
    if len(sealed)!=40 or len(outcomes)!=40 or set(sealed)!=set(outcomes):
        raise EvidenceBlocked("RESEARCH_COHORT_NOT_EXACT_40_TO_40")
    return sealed,outcomes

def audit(root):
    sealed,outcomes=collect(root)
    event_rows={g:{m:{e:[] for e in EVENTS} for m in MODELS} for g in GROUPS}
    availability=Counter();status=Counter();per_league=Counter()
    impossible_probability_count=0;complete=0
    model_1x2_scores=defaultdict(list)
    for key in sorted(sealed):
        record=outcomes[key];forecast=sealed[key]
        status[record["status"]]+=1
        for m in MODELS:
            prediction=forecast.get("model_predictions",{}).get(m,{})
            if prediction.get("status")=="AVAILABLE":
                # Probability and score-tails consistency are checked even if postponed.
                coherent(prediction["goals"]["markets"])
                availability[m]+=1
        if record["status"]=="POSTPONED":continue
        complete+=1;per_league[key[0]]+=1
        h,a=record["home_goals"],record["away_goals"]
        actual="H" if h>a else "D" if h==a else "A"
        group=("PRIMARY_ONLY" if record["source_class"]=="PRIMARY_LEAGUE_OR_CLUB"
               else "MEDIA_CROSSCHECKED")
        for m in MODELS:
            model=forecast.get("model_predictions",{}).get(m,{})
            if model.get("status")!="AVAILABLE":continue
            markets=model["goals"]["markets"]
            p1x2=coherent(markets)
            top=max(MS,key=lambda k:p1x2[k])
            model_1x2_scores[(m,"ALL_WEB_REVIEW")].append(sum(
                (p1x2[k]-int(k==actual))**2 for k in MS))
            if group=="PRIMARY_ONLY":
                model_1x2_scores[(m,"PRIMARY_ONLY")].append(sum(
                    (p1x2[k]-int(k==actual))**2 for k in MS))
            fields={
                "MS_TOP1":(p1x2[top],int(top==actual)),
                "MS1":(p1x2["H"],int(actual=="H")),
                "MSX":(p1x2["D"],int(actual=="D")),
                "MS2":(p1x2["A"],int(actual=="A")),
                "KG_VAR":(float(markets["BTTS_YES"]),int(h>0 and a>0)),
                "OVER_1.5":(float(markets["OVER_1.5"]),int(h+a>1.5)),
                "OVER_2.5":(float(markets["OVER_2.5"]),int(h+a>2.5)),
                "OVER_3.5":(float(markets["OVER_3.5"]),int(h+a>3.5)),
            }
            for e,(p,y) in fields.items():
                row={"p":probability(p),"y":y,
                    "match_day":utc(forecast["fixture"]["kickoff_utc"]).date().isoformat()}
                event_rows["ALL_WEB_REVIEW"][m][e].append(row)
                if group=="PRIMARY_ONLY":event_rows["PRIMARY_ONLY"][m][e].append(row)
    if complete!=39 or status["POSTPONED"]!=1:
        raise EvidenceBlocked("DIFFERENT_FROM_FROZEN_39_AND_ONE_POSTPONED")
    report={"schema":SCHEMA,
        "decision":"NO_PROOF_70_PERCENT_IS_TRUE_YET_RESEARCH_DESCRIPTIVE_ONLY",
        "cohort":{"seals":len(sealed),"results_web_reviewed":complete,
                  "postponed_excluded":status["POSTPONED"],
                  "source_primary_count":sum(v["source_class"]=="PRIMARY_LEAGUE_OR_CLUB" and v["status"]=="FULL_TIME" for v in outcomes.values()),
                  "source_media_crosschecked_count":sum(v["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL" and v["status"]=="FULL_TIME" for v in outcomes.values()),
                  "distinct_utc_match_days":len({r["match_day"] for r in event_rows["ALL_WEB_REVIEW"]["M4"]["MS_TOP1"]}),
                  "per_league":dict(per_league)},
        "model_availability_in_40_seals":dict(availability),
        "research_only_no_network_result_attestation":True,
        "results_matched_by_league_and_team_names_not_independent_final_canonical_ids":True,
        "all_available_score_market_probabilities_coherent":True,
        "by_evidence_class":{g:{m:{"markets":{e:summary(event_rows[g][m][e]) for e in EVENTS},
                            "MS_multiclass_Brier":round(sum(model_1x2_scores[(m,g)])/len(model_1x2_scores[(m,g)]),6)
                              if model_1x2_scores[(m,g)] else None,
                            "MS_n":len(model_1x2_scores[(m,g)])}
                         for m in MODELS} for g in GROUPS},
        "independent_70_percent_acceptance":False,
        "historical_896_pair_comparison_is_not_forward_calibration":True,
        "other_markets_are_correlated_do_not_pool_binomial_observations":True,
        "one_calendar_day_cannot_establish_reliable_calibration":True,
        "model_coefficients_or_probabilities_changed":False,
        "production_M4_updated":False,
        "recommendation":"Keep frozen M4, B/C2/C3 as recorded; measure each market on new dates using truly verified sealed source-ID outcomes, preserve PAS when unverified. Never derive a correction from this seen cohort."}
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    result=audit(args.root)
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if read(p)!=result:
            raise EvidenceBlocked("EXISTING_RESEARCH_AUDIT_DIFFERS_FROM_IMMUTABLE_RECOMPUTATION")
    else:
        p.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["decision"],"cohort":result["cohort"],
        "m4_top1_70band":result["by_evidence_class"]["PRIMARY_ONLY"]["M4"]["markets"]["MS_TOP1"]["confidence_65_75"],
        "m4_over25_70band":result["by_evidence_class"]["PRIMARY_ONLY"]["M4"]["markets"]["OVER_2.5"]["confidence_65_75"]},
        ensure_ascii=False),flush=True)

if __name__=="__main__":main()
