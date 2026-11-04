"""2.6.3: user-agreed four separate models, value-weighted main/alt/PAS (research only)."""
from __future__ import annotations
import argparse, json, math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from classification_odds_263 import GROUPS,canonical_markets,odds_evidence
from forward_baseline_provenance_263 import connect_verified_baseline
from forward_calibration_bridge_263 import _digest,MARKETS,CAL_SCHEMA
from forward_c3 import read_aware
from market_fifth_baseline_263 import OBSERVATION_SCHEMA,sealed_payload,fixture_key
from market_quote_intake_263 import ACCEPTED_DOMAINS

SCHEMA="263_four_model_value_decision_research_v1"
MODELS=("B","C2","C3","M4")
ALLOWED=("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5")
def family(m):
    return "MS" if m.startswith("MS") else "KG" if m.startswith("BTTS") else "GOALS"
def median(x):
    a=sorted(x);n=len(a);return (a[(n-1)//2]+a[n//2])/2
def _odds(obs,f,now):
    if obs is None:return {},"NO_VERIFIED_ODDS",None
    sealed_payload(obs,OBSERVATION_SCHEMA)
    if obs.get("evidence_scope")!="HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED":
        raise ValueError("HUMAN_ODDS_ATTESTATION_REQUIRED")
    if obs.get("forecast_payload_sha256")!=f["payload_sha256"] or obs.get("fixture_key")!=fixture_key(f["fixture"]):
        raise ValueError("ODDS_WRONG_FORECAST_OR_FIXTURE")
    domain=obs.get("source_domain")
    if domain not in ACCEPTED_DOMAINS:raise ValueError("ODDS_SOURCE_UNTRUSTED")
    rev=obs.get("source_review")
    if not isinstance(rev,dict) or rev.get("method")!="MANUAL_PUBLIC_PAGE" or not rev.get("reviewer") or not rev.get("visible_source_note"):
        raise ValueError("ODDS_HUMAN_OBSERVATION_MISSING")
    checked=read_aware(obs["analysis_at_utc"]);reviewed=read_aware(rev["reviewed_at_utc"])
    ko=read_aware(f["fixture"]["kickoff_utc"]);created=read_aware(f["created_at_utc"])
    if not created<=reviewed<=checked<=now<ko:raise ValueError("ODDS_NOT_PREMATCH")
    if (now-checked).total_seconds()>600:return {},"ODDS_STALE_OVER_10_MINUTES",None
    quotes=obs.get("quotes")
    if not isinstance(quotes,dict) or not quotes:return {},"NO_COMPLETE_ODDS",None
    if not set(quotes).issubset(ALLOWED):raise ValueError("ODDS_GROUP_NOT_ALLOWED")
    prices={}
    for group,quote in quotes.items():
        if quote.get("market_group")!=group or quote.get("fixture_key")!=obs["fixture_key"]:
            raise ValueError("ODDS_GROUP_FIXTURE_MISMATCH")
        parsed=urlparse(str(quote.get("source_url","")))
        if parsed.scheme!="https" or (parsed.hostname or "").lower().removeprefix("www.")!=domain or quote.get("source")!=domain:
            raise ValueError("ODDS_GROUP_SOURCE_MISMATCH")
        p={key:odds_evidence(key,quote,obs["fixture_key"],ko.isoformat(),now.isoformat())
           for key in GROUPS[group]}
        if any(x["status"]!="COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED" for x in p.values()):
            raise ValueError("ODDS_INCOMPLETE_OR_WRONG_MARGIN_"+group)
        for key,x in p.items():
            if key in MARKETS:prices[key]={"odds":x["decimal_odds"],"fair":x["no_vig"],"source":domain,
                                          "url":quote["source_url"],"checked":x["checked_at_utc"]}
    return prices,"HUMAN_ATTESTED_NOT_NETWORK_REVERIFIED",obs["payload_sha256"]

def decide(f,base,lock,observation=None,*,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    sealed_payload(f,"quad_forward_263_v1")
    if not read_aware(f["created_at_utc"])<=now<read_aware(f["fixture"]["kickoff_utc"]):
        raise ValueError("DECISION_AFTER_KICKOFF_OR_BEFORE_FORECAST")
    if set(f.get("model_predictions",{}))!=set(MODELS):raise ValueError("FOUR_MODELS_REQUIRED")
    if lock.get("schema")!=CAL_SCHEMA or lock.get("official_approval") is not False or lock.get("development_period")!="2026-08-01/2026-09-30":
        raise ValueError("FROZEN_DEV_LOCK_REQUIRED")
    if lock.get("payload_sha256")!=_digest({k:v for k,v in lock.items() if k!="payload_sha256"}):
        raise ValueError("FROZEN_DEV_LOCK_TAMPERED")
    # Uses the existing source, baseline and temporal provenance gate.
    # Its legacy M4-only preliminary pick is intentionally not reused.
    connect_verified_baseline(f,lock,base)
    if read_aware(base["created_at_utc"])>now:raise ValueError("BASELINE_FUTURE")
    prices,price_status,quote_sha=_odds(observation,f,now)
    raw={};scores={}
    for name in MODELS:
        m=f["model_predictions"][name]
        if m.get("status")=="AVAILABLE":
            raw[name]=canonical_markets(m["goals"]["markets"])
            scores[name]=m["goals"].get("top_scores",{})
        else:scores[name]={}
    out=[];qualified=[];alerts=[]
    for market in MARKETS:
        vals={name:p[market] for name,p in raw.items()}
        if not vals:continue
        b=base["markets"][market]
        support=sum(v>=b+.02 for v in vals.values())
        high=sum(v>=.75 for v in vals.values())>=3 and max(vals.values())-min(vals.values())<=.10
        if high:alerts.append({"market":market,"descriptive_raw_median":median(vals.values()),"not_a_bet":True})
        options=[]
        for model in ("M4","C3"):
            if model not in vals:continue
            skill=lock["calibration"][model][market]
            brier=skill.get("development_brier_skill")
            w=skill.get("weight")
            if skill.get("available") is True and skill.get("n",0)>=120 and isinstance(brier,(int,float)) and math.isfinite(brier) and brier>0:
                if not isinstance(w,(int,float)) or not 0<=w<=1:raise ValueError("INVALID_DEV_WEIGHT")
                options.append((brier,model,w))
        selected=max(options,key=lambda v:(v[0],v[1]=="M4")) if options else None
        anchor=selected[1] if selected else None
        q=b+selected[2]*(vals[anchor]-b) if selected else None
        price=prices.get(market)
        ev=q*price["odds"]-1 if price is not None and q is not None else None
        edge=q-price["fair"] if price is not None and q is not None else None
        reason=[]
        if len(vals)<3 or support<3:reason.append("UNDER_3_MODEL_SUPPORT")
        if selected is None:reason.append("NO_POSITIVE_DEV_BRIER_SKILL")
        elif q<.60 or q-b<.025:reason.append("LOW_CALIBRATED_LIFT")
        if price is None:reason.append("NO_SYNCHRONIZED_ODDS")
        elif q is not None and (ev<.05 or edge<.03):reason.append("EV_OR_NO_VIG_EDGE_FAIL")
        row={"market":market,"family":("MS" if market.startswith("MS") else "KG" if market.startswith("BTTS") else "GOALS"),
             "raw_model_probabilities":vals,"raw_median_diagnostic_only":median(vals.values()),
             "model_spread_pp":100*(max(vals.values())-min(vals.values())),"support_count":support,
             "strict_S1_75pct_3models_10pp_alert":high,"historical_base":b,
             "anchor_model":anchor,"dev_brier_skill":selected[0] if selected else None,
             "calibrated_probability":q,"observed_odds":price["odds"] if price else None,
             "EV":ev,"no_vig_advantage_pp":100*edge if edge is not None else None,
             "quote_source":price["source"] if price else None,
             "qualification_reasons":reason}
        out.append(row)
        if not reason:
            row["value_rank"]=ev+.10*(q-b)+.001*support
            qualified.append(row)
    qualified.sort(key=lambda x:(-x["value_rank"],-x["EV"],-x["calibrated_probability"],x["market"]))
    main=qualified[0] if qualified else None
    alt=next((x for x in qualified[1:] if x["family"]!=main["family"]),None) if main else None
    leader=max(("MS1","MSX","MS2"),key=lambda x:median([p[x] for p in raw.values()])) if raw else None
    result={"schema":SCHEMA,"status":"RESEARCH_VALUE_CANDIDATE_NOT_APPROVED" if main else "RESEARCH_PAS",
      "created_at_utc":now.isoformat(),"fixture":f["fixture"],
      "forecast_sha256":f["payload_sha256"],"baseline_sha256":base["payload_sha256"],
      "dev_lock_sha256":lock["payload_sha256"],"quote_sha256":quote_sha,
      "quote_status":price_status,"quote_reverified_by_code":False,
      "model_1x2":{k:{s:v[s] for s in ("MS1","MSX","MS2")} for k,v in raw.items()},
      "descriptive_most_likely_1x2_by_model_median":leader,"model_top_scores":scores,
      "high_probability_alerts_not_bets":alerts,"all_market_diagnostics":out,
      "main_candidate":main,"alternative_candidate":alt,
      "PAS_reasons":[] if main else ([price_status] if not prices else ["NO_QUALIFIED_VALUE_CANDIDATE"]),
      "no_arbitrary_1_5_over_penalty":True,
      "same_goal_family_never_separate_alternative":True,
      "frozen_dev_only_calibration":True,"B_C2_C3_M4_not_blended":True,
      "S1_S2_official_approved":False,"betting_authorized":False,
      "official_pilot_count_increment":0,"production_modified":False}
    result["payload_sha256"]=_digest(result)
    return result

def render(result):
    lines=["# Makina 2.6.3 — Dört model ve değer kararı (araştırma)",
           "**Resmî bahis onayı değildir.**",
           "En olası 1X2 (model medyanı, karar olasılığı değil): "+str(result["descriptive_most_likely_1x2_by_model_median"]),
           "Oran kanıtı: "+result["quote_status"],
           "| Model | MS1 | MSX | MS2 |","|---|---:|---:|---:|"]
    for m in MODELS:
        p=result["model_1x2"].get(m)
        lines.append("| "+m+" | "+(" | ".join(f"%{p[k]*100:.1f}" for k in ("MS1","MSX","MS2")) if p else "— | — | —")+" |")
    lines.append("Ana tercih (deneysel): "+(result["main_candidate"]["market"] if result["main_candidate"] else "PAS"))
    lines.append("Alternatif (ayrı aile): "+(result["alternative_candidate"]["market"] if result["alternative_candidate"] else "YOK"))
    if result["main_candidate"]:
        m=result["main_candidate"]
        lines.append(f"Olasılık %{m['calibrated_probability']*100:.1f} — Oran {m['observed_odds']} — EV %{m['EV']*100:+.1f} — Marjsız avantaj {m['no_vig_advantage_pp']:+.1f} puan")
    lines.append("PAS nedeni: "+", ".join(result["PAS_reasons"]))
    lines.append("1.5 Üst özel cezaya uğramaz; bütün pazarlar aynı kalibrasyon ve fiyat kontrollerinden geçer.")
    lines.append("Fiyat kaynağı insan gözlemidir, kod internetten bağımsız doğrulamaz.")
    return "\n\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    for field in ("forecast","baseline","dev-lock","out-dir"):p.add_argument("--"+field,required=True)
    p.add_argument("--odds")
    a=p.parse_args()
    read=lambda path:json.loads(Path(path).read_text(encoding="utf-8"))
    v=decide(read(a.forecast),read(a.baseline),read(getattr(a,"dev_lock")),
             read(a.odds) if a.odds else None)
    where=Path(a.out_dir)/v["fixture"]["match_local_date"]
    where.mkdir(parents=True,exist_ok=True)
    name=v["forecast_sha256"][:24]
    with (where/(name+".json")).open("x",encoding="utf-8") as f:json.dump(v,f,indent=2,ensure_ascii=False,sort_keys=True);f.write("\n")
    with (where/(name+".md")).open("x",encoding="utf-8") as f:f.write(render(v))
    print(json.dumps({"status":v["status"],"main":v["main_candidate"]["market"] if v["main_candidate"] else None,
        "alt":v["alternative_candidate"]["market"] if v["alternative_candidate"] else None},ensure_ascii=False))
if __name__=="__main__":main()
