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
from morning_quote_policy_263 import extract as extract_morning

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
    scope=obs.get("evidence_scope")
    is_provider=scope=="AGGREGATOR_API_NOT_DIRECT_BOOKMAKER_VERIFIED"
    if not is_provider and scope!="HUMAN_ATTESTED_NOT_EXTERNALLY_REVERIFIED":
        raise ValueError("ODDS_EVIDENCE_SCOPE_INVALID")
    if obs.get("forecast_payload_sha256")!=f["payload_sha256"] or obs.get("fixture_key")!=fixture_key(f["fixture"]):
        raise ValueError("ODDS_WRONG_FORECAST_OR_FIXTURE")
    domain=obs.get("source_domain")
    if domain not in ACCEPTED_DOMAINS:raise ValueError("ODDS_SOURCE_UNTRUSTED")
    rev=obs.get("source_review")
    if not isinstance(rev,dict) or not rev.get("reviewer") or not rev.get("visible_source_note"):
        raise ValueError("ODDS_SOURCE_OBSERVATION_MISSING")
    if is_provider:
        if (domain!="iddaa.com" or rev.get("method")!="ODDSPAPI_REST_RESPONSE"
            or rev.get("provider")!="oddspapi.io"
            or not isinstance(rev.get("provider_odds_sha256"),str)
            or len(rev["provider_odds_sha256"])!=64
            or not isinstance(rev.get("provider_fixture_id"),str)
            or not rev["provider_fixture_id"].startswith("id")):
            raise ValueError("ODDSPAPI_AGGREGATOR_PROVENANCE_INVALID")
    elif rev.get("method")!="MANUAL_PUBLIC_PAGE":
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
        if quote.get("verification")!=("PROVIDER_API_OBSERVED" if is_provider else "INDEPENDENTLY_CHECKED"):
            raise ValueError("ODDS_PROVENANCE_QUOTE_VERIFICATION_MISMATCH")
        p={key:odds_evidence(key,quote,obs["fixture_key"],ko.isoformat(),now.isoformat())
           for key in GROUPS[group]}
        expected=("COMPLETE_PREMATCH_QUOTES_PROVIDER_API_OBSERVED" if is_provider
                  else "COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED")
        if any(x["status"]!=expected for x in p.values()):
            raise ValueError("ODDS_INCOMPLETE_OR_WRONG_MARGIN_"+group)
        for key,x in p.items():
            if key in MARKETS:prices[key]={"odds":x["decimal_odds"],"fair":x["no_vig"],"source":domain,
                                          "url":quote["source_url"],"checked":x["checked_at_utc"]}
    return prices,("ODDSPAPI_AGGREGATOR_SOURCED_NOT_DIRECT_BOOKMAKER_VERIFIED" if is_provider
                   else "HUMAN_ATTESTED_NOT_NETWORK_REVERIFIED"),obs["payload_sha256"]

# Chosen from the two read-only historical comparisons on 20 Nov 2026.
# This is a fixed EXPERIMENTAL decision policy, not automatic model promotion.
# Never mix mutually exclusive 1/X/2 outcomes or complementary goal markets
# from different model vectors. All original B/C2/C3/M4 remain recorded.
FAMILY_EXPERTS={"MS":"M4","KG":"C3","GOALS":"C3"}
FAMILY_MEMBERS={
    "MS":("MS1","MSX","MS2"),
    "KG":("BTTS_YES","BTTS_NO"),
    "GOALS":("OVER_1.5","UNDER_1.5","OVER_2.5","UNDER_2.5","OVER_3.5","UNDER_3.5"),
}

def _validate_family(prob,family):
    if any(not isinstance(prob.get(m),(float,int)) or isinstance(prob.get(m),bool)
           or not math.isfinite(prob[m]) or not 0<=prob[m]<=1
           for m in FAMILY_MEMBERS[family]):
        raise ValueError("EXPERT_FAMILY_INVALID_PROBABILITY")
    if family=="MS" and abs(sum(prob[m] for m in FAMILY_MEMBERS["MS"])-1)>1e-7:
        raise ValueError("EXPERT_MS_NOT_NORMALIZED")
    if family=="KG" and abs(prob["BTTS_YES"]+prob["BTTS_NO"]-1)>1e-7:
        raise ValueError("EXPERT_KG_NOT_COMPLEMENTARY")
    if family=="GOALS":
        for line in ("1.5","2.5","3.5"):
            if abs(prob["OVER_"+line]+prob["UNDER_"+line]-1)>1e-7:
                raise ValueError("EXPERT_GOAL_LINE_NOT_COMPLEMENTARY")
        if not prob["OVER_1.5"]+1e-7>=prob["OVER_2.5"]>=prob["OVER_3.5"]-1e-7:
            raise ValueError("EXPERT_GOAL_LINES_NOT_MONOTONIC")

def _fixed_family_experts(raw,base,lock):
    """Fixed family routing with a single conservative frozen-dev shrinkage
    factor per COMPLETE family. This preserves MS sum=1, KG opposites and
    all three Over/Under complementary pairs. No fitted new parameters.
    Negative per-market skill can still block an EV/value candidate.
    """
    out={}
    for fam,preferred in FAMILY_EXPERTS.items():
        model=next((m for m in (preferred,"C3" if preferred=="M4" else "M4")
                    if m in raw),None)
        if model is None:continue
        members=FAMILY_MEMBERS[fam]
        model_vec={m:raw[model][m] for m in members}
        base_vec={m:base["markets"][m] for m in members}
        _validate_family(model_vec,fam)
        _validate_family(base_vec,fam)
        calibration=lock["calibration"][model]
        # Use the most conservative DEV weight among POSITIVE-SKILL
        # members. Negative-skill markets NEVER qualify for value, but
        # all family probabilities still receive this SAME weight.
        # This preserves %100 even when one goal line lacks skill.
        weights=[]
        for m in members:
            skill=calibration[m]
            brier=skill.get("development_brier_skill")
            if (skill.get("available") is not True or skill.get("n",0)<120
                or not isinstance(brier,(float,int)) or isinstance(brier,bool)
                or not math.isfinite(brier) or brier<=0):
                continue
            w=skill.get("weight")
            if (not isinstance(w,(float,int)) or isinstance(w,bool)
                or not math.isfinite(w) or not 0<=w<=1):
                raise ValueError("INVALID_EXPERT_DEV_WEIGHT")
            weights.append(w)
        common=min(weights) if weights else None
        softened=({m:base_vec[m]+common*(model_vec[m]-base_vec[m])
                   for m in members} if common is not None else None)
        if softened is not None:_validate_family(softened,fam)
        out[fam]={"model":model,"raw":model_vec,
                  "conservative_dev_family_weight":common,
                  "frozen_dev_shrunken":softened,
                  "eligible_for_further_value_gate":softened is not None}
    return out

def decide(f,base,lock,observation=None,*,morning_snapshot=None,pdf_first_snapshot=None,now=None):
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
    if pdf_first_snapshot is not None and (observation is not None or morning_snapshot is not None):
        raise ValueError("PDF_FIRST_CANNOT_MIX_OTHER_BOOKMAKERS_OR_PRICE_WINDOWS")
    fresh,price_status,quote_sha=_odds(observation,f,now)
    pdf_first={}
    if pdf_first_snapshot is not None:
        # Original iddaa PDF precedes the immutable forecast, unlike legacy
        # human post-forecast quotes. Local PDF SHA + exact fixture join are
        # independently checked by iddaa_pdf_first_quote_263.
        from iddaa_pdf_first_quote_263 import extract as extract_pdf_first
        pdf_first,price_status=extract_pdf_first(pdf_first_snapshot,f,now)
    morning=extract_morning(morning_snapshot,f,now) if morning_snapshot is not None else {}
    morning_sha=morning_snapshot["payload_sha256"] if morning_snapshot is not None else None
    # Same market: newer real price always wins, even when its EV falls.
    # Missing newer groups inherit old morning prices but stay conditional.
    prices={**morning,**pdf_first,**{k:{**v,"age_class":"CURRENT_T60","snapshot_sha256":quote_sha}
                         for k,v in fresh.items()}}
    raw={};scores={}
    for name in MODELS:
        m=f["model_predictions"][name]
        if m.get("status")=="AVAILABLE":
            raw[name]=canonical_markets(m["goals"]["markets"])
            scores[name]=m["goals"].get("top_scores",{})
        else:scores[name]={}
    experts=_fixed_family_experts(raw,base,lock)
    out=[];qualified=[];alerts=[]
    allowed=("MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO") if pdf_first_snapshot is not None else MARKETS
    for market in allowed:
        vals={name:p[market] for name,p in raw.items()}
        if not vals:continue
        b=base["markets"][market]
        support=sum(v>=b+.02 for v in vals.values())
        high=sum(v>=.75 for v in vals.values())>=3 and max(vals.values())-min(vals.values())<=.10
        if high:alerts.append({"market":market,"descriptive_raw_median":median(vals.values()),"not_a_bet":True})
        # Every market within a family uses the same expert, rather than
        # independently switching for 1, X and 2 (which broke normalization).
        fam=family(market)
        expert=experts.get(fam)
        anchor=expert["model"] if expert else None
        skill=lock["calibration"][anchor][market] if anchor else None
        brier=skill.get("development_brier_skill") if skill else None
        valid_dev=(skill is not None and skill.get("available") is True
                   and skill.get("n",0)>=120 and isinstance(brier,(float,int))
                   and not isinstance(brier,bool) and math.isfinite(brier)
                   and brier>0 and expert["frozen_dev_shrunken"] is not None)
        selected=(brier,anchor,expert["conservative_dev_family_weight"]) if valid_dev else None
        q=expert["frozen_dev_shrunken"][market] if selected else None
        price=prices.get(market)
        ev=q*price["odds"]-1 if price is not None and q is not None else None
        edge=q-price["fair"] if price is not None and q is not None else None
        reason=[]
        if len(vals)<3 or support<3:reason.append("UNDER_3_MODEL_SUPPORT")
        if selected is None:reason.append("NO_POSITIVE_DEV_BRIER_SKILL")
        elif q<.60 or q-b<.025:reason.append("LOW_CALIBRATED_LIFT")
        if price is None:reason.append("NO_VALID_PDF_QUOTE" if pdf_first_snapshot is not None else "NO_SYNCHRONIZED_ODDS")
        elif q is not None and (ev<.05 or edge<.03):reason.append("EV_OR_NO_VIG_EDGE_FAIL")
        row={"market":market,"family":("MS" if market.startswith("MS") else "KG" if market.startswith("BTTS") else "GOALS"),
             "raw_model_probabilities":vals,"raw_median_diagnostic_only":median(vals.values()),
             "model_spread_pp":100*(max(vals.values())-min(vals.values())),"support_count":support,
             "strict_S1_75pct_3models_10pp_alert":high,"historical_base":b,
             "anchor_model":anchor,"dev_brier_skill":selected[0] if selected else None,
             "fixed_specialist_model":anchor,
             "fixed_specialist_raw_probability":expert["raw"][market] if expert else None,
             "fixed_specialist_common_family_weight":expert["conservative_dev_family_weight"] if expert else None,
             "specialist_family_coherent":True if expert else False,
             "calibrated_probability":q,"observed_odds":price["odds"] if price else None,
             "EV":ev,"no_vig_advantage_pp":100*edge if edge is not None else None,
             "quote_source":price["source"] if price else None,
             "price_age_class":price.get("age_class") if price else None,
             "price_checked_at_utc":price.get("checked") if price else None,
             "price_snapshot_sha256":price.get("snapshot_sha256") if price else None,
             "qualification_reasons":reason}
        out.append(row)
        if not reason:
            row["value_rank"]=ev+.10*(q-b)+.001*support
            qualified.append(row)
    qualified.sort(key=lambda x:(-x["value_rank"],-x["EV"],-x["calibrated_probability"],x["market"]))
    main=qualified[0] if qualified else None
    alt=next((x for x in qualified[1:] if x["family"]!=main["family"]),None) if main else None
    leader=max(("MS1","MSX","MS2"),key=lambda x:median([p[x] for p in raw.values()])) if raw else None
    conditional_classes=("MORNING_ARCHIVE_NOT_CURRENT","ARCHIVED_PDF_PRE_FORECAST")
    main_old=bool(main and main["price_age_class"] in conditional_classes)
    alt_old=bool(alt and alt["price_age_class"] in conditional_classes)
    stage=("RESEARCH_CONDITIONAL_IDDAA_PDF_PRICE_NOT_CURRENT"
           if main_old and pdf_first_snapshot is not None else
           "RESEARCH_CONDITIONAL_MORNING_PRICE_NOT_CURRENT" if main_old else
           "RESEARCH_VALUE_CANDIDATE_NOT_APPROVED" if main else "RESEARCH_PAS")
    result={"schema":SCHEMA,"status":stage,
      "created_at_utc":now.isoformat(),"fixture":f["fixture"],
      "forecast_sha256":f["payload_sha256"],"baseline_sha256":base["payload_sha256"],
      "dev_lock_sha256":lock["payload_sha256"],"quote_sha256":quote_sha,
      "morning_quote_sha256":morning_sha,
      "iddaa_pdf_first_sha256":pdf_first_snapshot.get("payload_sha256") if pdf_first_snapshot is not None else None,
      "iddaa_original_pdf_sha256":pdf_first_snapshot.get("source_pdf_sha256") if pdf_first_snapshot is not None else None,
      "iddaa_pdf_only_seven_markets":pdf_first_snapshot is not None,
      "morning_quote_status":"MORNING_ARCHIVE_NOT_CURRENT" if morning else "NO_MORNING_ARCHIVE",
      "main_value_conditional":main_old,"main_price_current":bool(main and not main_old),
      "alternative_value_conditional":alt_old,
      "alternative_price_current":bool(alt and not alt_old),
      "any_selected_value_conditional":main_old or alt_old,
      "morning_and_fresh_mixed_by_market":bool(morning and fresh),
      "iddaa_pdf_pre_forecast_not_live":pdf_first_snapshot is not None,
      "current_bookmaker_odds_not_reverified":pdf_first_snapshot is not None,
      "quote_status":price_status,"quote_reverified_by_code":False,
      "fixed_market_specialists_research_only":{f:{"model":e["model"],
          "raw_probabilities":e["raw"],
          "common_dev_family_weight":e["conservative_dev_family_weight"],
          "dev_shrunken_probability_vector":e["frozen_dev_shrunken"]}
          for f,e in experts.items()},
      "MS_three_outcomes_single_expert_normalized":bool("MS" in experts),
      "fixed_market_specialists_not_meta_learner":True,
      "not_officially_promoted":True,
      "model_1x2":{k:{s:v[s] for s in ("MS1","MSX","MS2")} for k,v in raw.items()},
      "descriptive_most_likely_1x2_by_model_median":leader,"model_top_scores":scores,
      "high_probability_alerts_not_bets":alerts,"all_market_diagnostics":out,
      "main_candidate":main,"alternative_candidate":alt,
      "PAS_reasons":[] if main else (["NO_MORNING_OR_CURRENT_ODDS"] if not prices else ["NO_QUALIFIED_VALUE_CANDIDATE"]),
      "old_price_EV_is_historical_scenario_only":True,
      "no_arbitrary_1_5_over_penalty":pdf_first_snapshot is None,
      "user_pdf_markets_1_5_and_3_5_excluded":pdf_first_snapshot is not None,
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
           "Sabah arşivi: "+result.get("morning_quote_status","NO_MORNING_ARCHIVE"),
           "Ana tercih fiyat durumu: "+("PDF ÖNCE ALINDI — fiyat koşullu, güncelliği doğrulanmadı" if result.get("iddaa_pdf_only_seven_markets") and result.get("main_value_conditional") else "SABAH FİYATIYLA KOŞULLU — güncel fiyat doğrulanmadı"
               if result.get("main_value_conditional") else "GÜNCEL FİYAT VEYA PAS"),
           "Alternatif fiyat durumu: "+("SABAH FİYATIYLA KOŞULLU — güncel fiyat doğrulanmadı"
               if result.get("alternative_value_conditional") else
               "GÜNCEL FİYAT" if result.get("alternative_price_current") else "YOK"),
           "| Model | MS1 | MSX | MS2 |","|---|---:|---:|---:|"]
    for m in MODELS:
        p=result["model_1x2"].get(m)
        lines.append("| "+m+" | "+(" | ".join(f"%{p[k]*100:.1f}" for k in ("MS1","MSX","MS2")) if p else "— | — | —")+" |")
    specialist=result.get("fixed_market_specialists_research_only",{})
    if specialist:
        lines.append("Pazar uzmanı (araştırma): "+", ".join(
            f"{fam}={item['model']}" for fam,item in specialist.items()))
        ms=specialist.get("MS",{}).get("dev_shrunken_probability_vector")
        if ms:
            lines.append("Tek modelden tutarlı MS 1/X/2: "+
                         " / ".join(f"%{ms[k]*100:.1f}" for k in ("MS1","MSX","MS2"))+
                         " (toplam %100; resmî bahis onayı değil)")
    lines.append("Ana tercih (deneysel): "+(result["main_candidate"]["market"] if result["main_candidate"] else "PAS"))
    lines.append("Alternatif (ayrı aile): "+(result["alternative_candidate"]["market"] if result["alternative_candidate"] else "YOK"))
    if result["alternative_candidate"]:
        a=result["alternative_candidate"]
        lines.append(f"Alternatif olasılık %{a['calibrated_probability']*100:.1f} — Oran {a['observed_odds']} ({a['price_age_class']}, {a['price_checked_at_utc']}) — EV %{a['EV']*100:+.1f}")
        if result.get("alternative_value_conditional"):
            lines.append("Alternatif EV yalnızca kayıtlı İddaa PDF fiyatındaki koşullu değerdir; canlı fiyat değildir."
                if result.get("iddaa_pdf_only_seven_markets") else
                "Alternatif EV yalnızca SABAH fiyatındaki varsayımsal değerdir; güncel fiyatı doğrulanmadı.")
    if result["main_candidate"]:
        m=result["main_candidate"]
        lines.append(f"Olasılık %{m['calibrated_probability']*100:.1f} — Oran {m['observed_odds']} ({m['price_age_class']}, {m['price_checked_at_utc']}) — EV %{m['EV']*100:+.1f} — Marjsız avantaj {m['no_vig_advantage_pp']:+.1f} puan")
        if result.get("main_value_conditional"):
            lines.append("Bu EV yalnızca kayıtlı İddaa PDF fiyatıyla araştırma senaryosudur; maç saatinde aynı fiyatın alınabildiği doğrulanmadı."
                if result.get("iddaa_pdf_only_seven_markets") else
                "Bu EV yalnızca SABAH fiyatıyla senaryo değeridir; maç saatinde aynı fiyatın alınabildiği doğrulanmadı.")
    lines.append("PAS nedeni: "+", ".join(result["PAS_reasons"]))
    if result.get("iddaa_pdf_only_seven_markets"):
        lines.append("Kapsam yalnız MS 1/X/2, KG Var/Yok ve 2.5 Alt/Üst. PDF fiyatları tahminden ÖNCE arşivlenmiştir; canlı fiyat değildir.")
    else:
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
