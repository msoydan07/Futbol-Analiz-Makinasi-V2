"""Read-only 2.6.3 report overlay: canonical C2 × analysis-time odds/A-B-C.

This adapter does not fetch odds or attest their authenticity. The existing
17-section offline acceptance is preserved, never turned into a LIVE PASS.
No forecast or pilot ledger is written; other models cannot replace C2.
"""
from __future__ import annotations
from datetime import datetime, timezone
from classification_odds_263 import MARKETS, classify, explain, aware

VERSION="263_readonly_analysis_time_decision_appendix_v1"


class BridgeError(ValueError):pass


def offline_appendix(verified_context:dict, bundle:dict, now:datetime) -> dict:
    """Add an honest no-quote A/B/C explanation to an official named fixture preview.

    Real-time quotes need a separate independently inspected source. This adapter
    accepts NO caller-provided 'verified odds' booleans or arbitrary quote JSON.
    """
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise BridgeError("aware_analysis_time_required")
    if verified_context.get("status")!="READY_FOR_DATA_AUDIT":
        raise BridgeError("official_fixture_gate_not_ready")
    fixture=verified_context["fixture"]
    if not (bundle.get("scope")=="HYPOTHETICAL_OFFLINE_AUDIT" and
            bundle.get("not_live_match_analysis") is True and
            bundle.get("real_fixture_verified") is False and
            bundle.get("recommendations")==[] and bundle.get("odds_EV") is None):
        raise BridgeError("offline_bundle_contract_mismatch")
    cases=bundle.get("cases")
    if not isinstance(cases,list) or len(cases)!=1:raise BridgeError("one_named_match_only")
    entry=cases[0];ident=entry["identity"]
    if (ident["league"],ident["home_id"],ident["away_id"],ident["target_date"]) != (
        fixture["league"],fixture["home_id"],fixture["away_id"],fixture["local_date"]):
        raise BridgeError("fixture_and_model_identity_disagree")
    ts=aware(now.isoformat());kickoff=aware(fixture["kickoff_utc"])
    if ts>=kickoff:raise BridgeError("analysis_no_longer_prematch")
    model=entry["analysis"]["model_outputs"].get("C2")
    out={"version":VERSION,"status":"OFFLINE_ANALYSIS_APPENDIX_NO_LIVE_PRICE_OR_ABC_APPROVAL",
         "fixture":{"league":fixture["league"],"home_id":fixture["home_id"],
                    "away_id":fixture["away_id"],"kickoff_utc":kickoff.isoformat(),
                    "official_fixture_source":fixture["source_url"]},
         "analysis_at_utc":ts.isoformat(),
         "odds_policy":"CHECK_SOURCE_AT_ANALYSIS_TIME_MAX_10_MIN_OLD; NO_LATER_REFRESH",
         "model":"C2_CANONICAL_ONLY_NO_FALLBACK",
         "data_status":"FROZEN_HISTORICAL_NOT_LIVE_ACCEPTED",
         "price_source_status":"LIVE_PRICE_NOT_FETCHED",
         "lineups":verified_context["facts"]["lineups"]["status"],
         "lineups_not_published_blocks_math":False,
         "recommendations":[],"approved_classes":[],
         "pilot_registered":False,"production_modified":False,
         "comparators_not_promoted":["B","C3","M4"],
         "rows":[]}
    if model is None:
        out["model_status"]="UNAVAILABLE_C2_CONTEXT_LT_4_OR_MODEL_ERROR"
        return out
    goals=model["goals"];detail=model["details"]
    if goals["lambda_home"]!=detail["lambda_home"] or goals["lambda_away"]!=detail["lambda_away"]:
        raise BridgeError("c2_lambda_cross_field_mismatch")
    if entry["decision_preflight_263"]["canonical_model"]!="C2":
        raise BridgeError("canonical_model_readiness_mismatch")
    out["model_status"]="CALCULATED_NOT_FORWARD_CALIBRATED"
    for market in MARKETS:
        result=classify(model="C2",markets=goals["markets"],selection=market,
                        lambda_home=detail["lambda_home"],
                        lambda_away=detail["lambda_away"],
                        fixture_key=fixture["league"]+":"+fixture["home_id"]+":"+fixture["away_id"]+":"+fixture["local_date"],
                        kickoff=fixture["kickoff_utc"],now=ts.isoformat(),league=fixture["league"],
                        model_level="BASIT",data_reliability="DOGRULANAMADI",
                        context_ok=False,critical_unverified_effect=False,
                        fixture_verified=True,quote=None)
        if (result["candidate_class"]!="DEGERLENDIRILEMEDI" or
                result["official_class"] is not None or result["EV"] is not None or
                result["pilot_registered"]):
            raise BridgeError("offline_report_claimed_approved_class")
        out["rows"].append(result)
    return out


def render_appendix(appendix:dict) -> str:
    if appendix.get("status")!="OFFLINE_ANALYSIS_APPENDIX_NO_LIVE_PRICE_OR_ABC_APPROVAL":
        raise BridgeError("invalid_appendix")
    lines=["## §12–14 — Analiz anı oranı ve A/B/C bağlantısı (henüz onaysız)","",
           "**Bu ek gerçek zamanlı oran sorgusu değildir; mevcut tarihsel rapora bağlanmış güvenli hazırlıktır.**",
           "Gerçek maç analizinde oran, analiz anında doğrulanacak; kontrol saati ve kaynak belirtilir.",
           "Analizden sonra oran değişirse bu önceki değerlendirmeyi değiştirmez.",
           "C2 dışındaki B/C3/M4 modelleri otomatik ana model yapılmadı.",
           "**Oran/EV:** DOĞRULANAMADI — kaynak sorgulanmadı. **Resmî A/B/C:** ONAYSIZ.",
           "İlk 11 yokluğu analiz matematiğini durdurmaz.",
           ""]
    if not appendix["rows"]:
        lines.append("C2 mevcut değil. Karar sınıflandırması üretilemedi.")
    else:
        lines+=["| Pazar | C2 matematik olasılığı | Oran (analiz anı) | Sınıf |",
                "|---|---:|---|---|"]
        for row in appendix["rows"]:
            lines.append("| "+row["selection"]+" | %"+format(100*row["model_probability"],".1f")+
                         " | DOĞRULANAMADI | DEĞERLENDİRİLEMEDİ |")
    lines.append("")
    lines.append("Bağımsız güncel veri, fiyat ve model kalibrasyonu olmadan bahis/değer onayı yoktur; pilot kaydı oluşturulmadı.")
    return "\n".join(lines)
