"""Single user-facing result order for PREMATCH 2.6.3, read-only trial.

Current renderer supports the one SHA-locked Nov 4 EARLY SHADOW example ONLY.
Never infers S1/S2 from a probability, an old aggregator quote or market closeness.
Does NOT re-fit, select, promote or overwrite any model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

VERSION="263_user_result_view_v1"
FORECAST_SHA="1038b6e9cd1f0bcbceb97367e261bc579b07a56e4e2dc5193c2f247e51e18ffb"
QUOTE_SCHEMA="263_secondary_market_price_research_v1"
MARKETS={"MS":{"MS1":"MS 1","MSX":"MS X","MS2":"MS 2"},
         "GOALS_2.5":{"UNDER_2.5":"2,5 Alt","OVER_2.5":"2,5 Üst"},
         "KG":{"BTTS_YES":"KG Var","BTTS_NO":"KG Yok"}}
MODELS=("B","C2","C3","M4")
MS_KEYS={"MS1":"H","MSX":"D","MS2":"A"}


def _canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),
                      allow_nan=False).encode("utf-8")


def _p(x):
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not 0<=x<=1:
        raise ValueError("NON_FINITE_OR_BAD_PROBABILITY")
    return float(x)


def _fmt(x):
    return f"%{100*x:.1f}".replace(".",",")


def build(shadow, price=None):
    if shadow.get("schema")!="quad_forward_263_v1" or shadow.get("payload_sha256")!=FORECAST_SHA:
        raise ValueError("ONLY_EXISTING_SHA_SEALED_EARLY_SHADOW")
    without={k:v for k,v in shadow.items() if k!="payload_sha256"}
    if hashlib.sha256(_canonical(without)).hexdigest()!=FORECAST_SHA:
        raise ValueError("ALTERED_EXISTING_FORECAST")
    if (shadow.get("status")!="EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING"
        or shadow.get("data",{}).get("human_source_acceptance") is not False
        or shadow["data"].get("research_shadow_unverified_source") is not True):
        raise ValueError("UNVERIFIED_STAGE_IS_NOT_A_PILOT_RECORD")
    if set(shadow["model_predictions"])!=set(MODELS):
        raise ValueError("FOUR_MODEL_RECORD_REQUIRED")
    fixture=shadow["fixture"]
    if (fixture["league"]!="TUR1" or fixture["match_local_date"]!="2026-11-06"
        or fixture["kickoff_utc"]!="2026-11-06T17:00:00+00:00"):
        raise ValueError("NOT_THIS_EXAMPLE_FIXTURE")
    forecast={}
    for name in MODELS:
        record=shadow["model_predictions"][name]
        if record["status"]!="AVAILABLE":
            raise ValueError("MISSING_EARLY_SHADOW_MODEL")
        m=record["goals"]["markets"]
        probs={
            "MS1":_p(m["1X2"]["H"]),"MSX":_p(m["1X2"]["D"]),
            "MS2":_p(m["1X2"]["A"]),
            "UNDER_2.5":_p(m["UNDER_2.5"]),"OVER_2.5":_p(m["OVER_2.5"]),
            "BTTS_YES":_p(m["BTTS_YES"]),"BTTS_NO":_p(m["BTTS_NO"]),
        }
        if abs(sum(probs[k] for k in ("MS1","MSX","MS2"))-1)>1e-5:
            raise ValueError("INVALID_SUM_MS")
        forecast[name]=probs
    markets={}
    if price is not None:
        if (price.get("schema")!=QUOTE_SCHEMA or
            price.get("quote_source_tier")!="SECONDARY_AGGREGATOR_UNVERIFIED" or
            price.get("direct_bookmaker_confirmation") is not False or
            price.get("single_synchronized_market_observation_proven") is not False or
            price.get("eligible_for_live_quote_lock") is not False or
            price.get("eligible_for_S1_S2") is not False or
            price.get("source_provider")!="OddsFilter (aggregator; not bookmaker)" or
            price.get("fixture",{}).get("kickoff_utc")!=fixture["kickoff_utc"]):
            raise ValueError("SECONDARY_PRICE_CANNOT_BE_PRESENTED_AS_CURRENT")
        for group,labels in MARKETS.items():
            raw=price["price_markets"][group]
            if set(raw)!=set(labels):
                raise ValueError("MISSING_COUNTERPRICES")
            if any(isinstance(o,bool) or not isinstance(o,(int,float)) or not math.isfinite(o) or not 1<o<=1000 for o in raw.values()):
                raise ValueError("BAD_QUOTE")
            total=sum(1/x for x in raw.values())
            if not 1<total<1.45:
                raise ValueError("BAD_MARKET_MARGIN")
            fair={k:(1/v)/total for k,v in raw.items()}
            markets[group]={"source":"UNVERIFIED_SECONDARY", "fair":fair,
                            "margin":total-1, "odds":raw}
    return {
        "schema":VERSION,
        "match":"Gaziantep FK – Kasımpaşa",
        "kickoff_turkey":"06.11.2026 20:00",
        "recorded_at_utc":shadow["created_at_utc"],
        "forecast_sha256":FORECAST_SHA,
        "official_fixture_verified":True,
        "data_quality":"MACHINE_STAGED_4509_NOT_HUMAN_ACCEPTED",
        "forecast_record_type":"EARLY_RESEARCH_NOT_OFFICIAL_96_PILOT",
        "s1":{"status":"ONAYSIZ","reason":"Güncel kaynak kabulü ve ileri olasılık kalibrasyonu henüz tamam değil."},
        "s2":{"status":"HESAPLANAMAZ","reason":"Güncel, aynı-anlı, doğrudan doğrulanmış tam karşı fiyatlar yok."},
        "market_role":"REFERENCE_RESEARCH_ONLY_NOT_MODEL_SELECTION",
        "market":markets,
        "models":forecast,
        "nearest_market_model_does_not_count_as_recommendation":True,
        "betting_authorized":False,
        "pilot_count_increment":0,
        "model_parameters_modified":False,
    }


def render(result):
    if (result.get("schema")!=VERSION or result.get("betting_authorized") is not False
        or result.get("pilot_count_increment")!=0):
        raise ValueError("UNSAFE_PRESENTATION")
    md=[
        "# Maç Analiz Makinası 2.6.3 — Tek Bakışta Sonuç",
        "",
        f"**{result['match']}** · {result['kickoff_turkey']} (TSİ)",
        "",
        "## 1. KARAR EKRANI",
        "",
        "**Genel durum: ONAYLI TERCİH YOK — erken araştırma kaydı.**",
        "",
        f"**S1 · En olası tercih:** {result['s1']['status']}. {result['s1']['reason']}",
        "",
        f"**S2 · Matematiksel değer:** {result['s2']['status']}. {result['s2']['reason']}",
        "",
        "_Burada yüksek bir yüzde görmek, bahis için onaylı seçim demek değildir._",
        "",
        "## 2. PİYASA İLE AYRIŞMA — araştırma",
        "",
    ]
    ms=result["market"].get("MS")
    if ms is None:
        md.append("Güncel piyasa fiyatı **DOĞRULANAMADI**. Bu bölümde bir model seçilmez.")
    else:
        fair=ms["fair"];p=result["models"]["M4"]
        md.extend([
          "**İkincil eski fiyatlar — canlı/aynı anlı bahis oranı değildir.**",
          "",
          "| Maç sonucu | Piyasa marjsız | M4 erken tahmini | Fark |",
          "|---|---:|---:|---:|",
          *[f"| {MARKETS['MS'][k]} | {_fmt(fair[k])} | {_fmt(p[k])} | {(p[k]-fair[k])*100:+.1f} yp |".replace(".",",")
            for k in MARKETS["MS"]],
          "",
          "Piyasaya yakınlık **başarı kanıtı veya otomatik model seçimi değildir**.",
        ])
    md.extend([
      "",
      "## 3. DÖRT MODEL — teknik ayrıntı",
      "",
      "| Model | MS 1 | MS X | MS 2 | 2,5 Alt | KG Var |",
      "|---|---:|---:|---:|---:|---:|",
    ])
    for name in MODELS:
        p=result["models"][name]
        md.append("| "+" | ".join([name,*(_fmt(p[k]) for k in ("MS1","MSX","MS2","UNDER_2.5","BTTS_YES"))])+" |")
    md.extend([
      "",
      "## 4. KAYIT VE GÜVENİLİRLİK",
      "",
      f"- Tahmin kaydı (UTC): `{result['recorded_at_utc']}`",
      f"- SHA-256: `{result['forecast_sha256']}`",
      "- Resmî fikstür onaylandı; sonuç verisi yalnız makine bütünlük aşamasında, **insan kaynak onayı yok**.",
      "- Bu kayıt **96 maçlık resmî T−60 pilotuna dahil değil**.",
      "- S1/S2 seçimleri, bahis kararı, gerçek para işlemi veya model terfisi oluşturulmadı.",
      "",
      "### Maç sonu raporu (ayrı ekran)",
      "Sonuç belli olduğunda sadece **önceden mühürlü** tahmin–gerçek sonuç ve Brier/log-loss kıyası gösterilir. Eski tahmin değiştirilmez.",
    ])
    return "\n".join(md)+"\n"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--forecast",required=True)
    ap.add_argument("--secondary-quote")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    source=json.loads(Path(a.forecast).read_text(encoding="utf-8"))
    price=json.loads(Path(a.secondary_quote).read_text(encoding="utf-8")) if a.secondary_quote else None
    output=render(build(source,price))
    p=Path(a.out)
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise SystemExit("REFUSE_OVERWRITE_EXISTING_PRESENTATION")
    p.write_text(output,encoding="utf-8")
    print(f"USER_RESULT_VIEW_OK bytes={len(output)} SHA={FORECAST_SHA}")


if __name__=="__main__":main()
