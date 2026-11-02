"""Read-only four-model market baseline. Proximity NEVER chooses the main model."""
from classification_odds_263 import GROUPS, canonical_markets, odds_evidence, DecisionError

MODELS=("B","C2","C3","M4")
MARKETS=("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5")
VERSION="263_market_reference_nonpromoting_v1"
VALID_PRICE="COMPLETE_PREMATCH_QUOTES_SOURCE_FLAGGED_AS_CHECKED"

class MarketReferenceError(ValueError):pass

def compare(*,models,quote,fixture_key,kickoff,now):
    if not isinstance(models,dict) or set(models)!=set(MODELS):
        raise MarketReferenceError("REQUIRES_EXACT_FOUR_MODEL_OUTPUTS")
    if not isinstance(fixture_key,str) or not fixture_key.strip():
        raise MarketReferenceError("FIXTURE_ID_REQUIRED")
    common={"version":VERSION,"fixture_key":fixture_key,
            "model_selected":False,"models_promoted":[],
            "A_B_C_approved":False,"recommendations":[],
            "pilot_recorded":False,"main_model_changed":False}
    if quote is None:
        return {**common,"status":"NO_VERIFIED_COMPLETE_ANALYSIS_TIME_ODDS",
                "reason":"No quote supplied","model_comparison":[],
                "closest_per_selection":{},"closest_full_market":[]}
    if not isinstance(quote,dict):raise MarketReferenceError("QUOTE_MUST_BE_SNAPSHOT")
    group=quote.get("market_group")
    if group not in MARKETS:raise MarketReferenceError("EXCLUSIVE_MARKET_REQUIRED")
    selections=GROUPS[group]
    prices={k:odds_evidence(k,quote,fixture_key,kickoff,now) for k in selections}
    if any(x["status"]!=VALID_PRICE for x in prices.values()):
        return {**common,"status":"NO_VERIFIED_COMPLETE_ANALYSIS_TIME_ODDS",
                "market_group":group,
                "reason":{k:v["status"] for k,v in prices.items()},
                "model_comparison":[],"closest_per_selection":{},"closest_full_market":[]}
    p_market={k:prices[k]["no_vig"] for k in selections}
    if abs(sum(p_market.values())-1)>1e-8:
        raise MarketReferenceError("INVALID_MARKET_NORMALIZATION")
    rows=[]
    for name in MODELS:
        model=models[name]
        if not isinstance(model,dict):
            raise MarketReferenceError("MALFORMED_MODEL_RECORD")
        if model.get("status")!="AVAILABLE":
            rows.append({"model":name,"status":"UNAVAILABLE",
                         "reason":str(model.get("reason",model.get("status","unknown")))})
            continue
        goals=model.get("goals")
        if not isinstance(goals,dict):
            raise MarketReferenceError("AVAILABLE_MODEL_MISSING_GOALS")
        try:
            p=canonical_markets(goals["markets"])
        except (KeyError,TypeError,DecisionError) as exc:
            raise MarketReferenceError("INVALID_MODEL_MARKETS_"+name) from exc
        choices=[]
        for selection in selections:
            value=p[selection];market=p_market[selection]
            odds=prices[selection]["decimal_odds"]
            choices.append({"selection":selection,"model_probability":value,
                "no_vig_market_probability":market,
                "model_fair_odds":1/value if value>0 else None,
                "observed_bookmaker_price":odds,
                "difference_percentage_points":100*(value-market),
                "absolute_difference_pp":100*abs(value-market),
                "arithmetic_ev_not_a_value_approval":value*odds-1})
        rows.append({"model":name,"status":"COMPARABLE",
                     "mean_abs_gap_pp":sum(c["absolute_difference_pp"] for c in choices)/len(choices),
                     "selections":choices})
    available=[r for r in rows if r["status"]=="COMPARABLE"]
    full=[]
    if available:
        low=min(r["mean_abs_gap_pp"] for r in available)
        full=[r["model"] for r in available if abs(r["mean_abs_gap_pp"]-low)<1e-9]
    per={}
    for sel in selections:
        gaps={r["model"]:next(c["absolute_difference_pp"] for c in r["selections"]
                              if c["selection"]==sel) for r in available}
        if gaps:
            low=min(gaps.values())
            per[sel]=[name for name in MODELS if name in gaps and abs(gaps[name]-low)<1e-9]
        else:per[sel]=[]
    first=prices[selections[0]]
    return {**common,
        "status":"DESCRIPTIVE_ONLY_NOT_MODEL_SELECTION",
        "market_group":group,"price_source":first["source"],
        "source_url":first["source_url"],
        "checked_at_utc":first["checked_at_utc"],
        "analysis_at_utc":first["analysis_at_utc"],
        "source_flag_does_not_prove_independent_live_check":True,
        "normalization":"proportional_no_vig",
        "market_margin":first["market_margin"],
        "observed_prices":{k:prices[k]["decimal_odds"] for k in selections},
        "no_vig_probabilities":p_market,
        "model_comparison":rows,
        "closest_per_selection":per,
        "closest_full_market":full,
        "closest_does_not_mean_best_model":True,
        "comparison_changes_no_probabilities":True}

def render(result):
    if result["status"]!="DESCRIPTIVE_ONLY_NOT_MODEL_SELECTION":
        return "Piyasa kıyası: DOĞRULANAMADI (tam ve güncel karşı oranlar gerekli)."
    out=["## B/C2/C3/M4 piyasa referansı (bilgilendirme)",
         "En yakın model otomatik ana model seçilmez; A/B/C veya bahis onayı verilmez.",
         "Kaynak: "+str(result["price_source"])+
         "; analiz anı fiyat kontrolü (UTC): "+str(result["checked_at_utc"]),
         "| Model | Ortalama fark (puan) | Durum |","|---|---:|---|"]
    for row in result["model_comparison"]:
        if row["status"]=="COMPARABLE":
            out.append("| "+row["model"]+" | "+format(row["mean_abs_gap_pp"],".2f")+" | Kıyaslandı |")
        else:out.append("| "+row["model"]+" | — | Veri yetersiz |")
    out+=["","Piyasaya en yakın (betimsel): "+", ".join(result["closest_full_market"]),
          "Piyasa yakınlığı, sonuç tahmini başarısını kanıtlamaz. Kayıt yok."]
    return "\n".join(out)
