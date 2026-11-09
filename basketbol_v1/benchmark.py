"""Prequential research: choose using dev season, compare on later holdout."""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from engine import VARIANTS,replay,before_game
from sources import download,SourceError
SPLIT={"NBA":{"development":2025,"heldout":2026,"current_replay":2027},
       "EL":{"development":2024,"heldout":2025,"current_replay":2026}}
def grade(rows):
    n=len(rows)
    if not n:
        return {"n":0,"correct":0,"accuracy":None,"brier":None,"logloss":None,
                "margin_mae":None,"total_mae":None,"margin_rmse":None,"total_rmse":None}
    right=brier=loss=mae_m=mae_t=sse_m=sse_t=0.0
    for g,p in rows:
        y=int(g.margin>0);pr=p.home_win()
        right+=int((pr>=.5)==bool(y))
        brier+=(pr-y)**2
        loss-=math.log(pr if y else 1-pr)
        mae_m+=abs(p.margin-g.margin);mae_t+=abs(p.total-g.total)
        sse_m+=(p.margin-g.margin)**2;sse_t+=(p.total-g.total)**2
    return {"n":n,"correct":int(right),"accuracy":round(right/n,5),
            "brier":round(brier/n,6),"logloss":round(loss/n,6),
            "margin_mae":round(mae_m/n,4),"total_mae":round(mae_t/n,4),
            "margin_rmse":round(math.sqrt(sse_m/n),4),
            "total_rmse":round(math.sqrt(sse_t/n),4)}
def choose_dev(d):
    base=d["BASE"]
    if base["n"]<150:raise ValueError("INSUFFICIENT_DEVELOPMENT_DATA")
    if min(base["brier"],base["margin_mae"],base["total_mae"])<=0:raise ValueError("BASELINE_INVALID")
    def obj(g):
        return .5*g["brier"]/base["brier"]+.25*g["margin_mae"]/base["margin_mae"]+.25*g["total_mae"]/base["total_mae"]
    return (min(VARIANTS,key=lambda name:(obj(d[name]),VARIANTS.index(name))),
            {name:round(obj(d[name]),6) for name in VARIANTS})
def league_benchmark(games,league,manifest):
    rows=replay(games)
    batches=defaultdict(list);split=SPLIT[league]
    for g,p in rows:
        stage=next((name for name,s in split.items() if g.season==s),None)
        if stage:batches[(stage,p.variant)].append((g,p))
    metrics={stage:{name:grade(batches[(stage,name)]) for name in VARIANTS}
             for stage in split}
    choice,obj=choose_dev(metrics["development"])
    if metrics["heldout"][choice]["n"]<150:raise ValueError("INSUFFICIENT_LOCKED_HOLDOUT")
    if any(len({metrics[stage][name]["n"] for name in VARIANTS})!=1 for stage in split):
        raise ValueError("UNEQUAL_COMPARISON_GAME_COUNTS")
    return {"league":league,"regulation_minutes":48 if league=="NBA" else 40,
            "historical_game_count":len(games),"source_manifest":manifest,
            "split_seasons":split,"development_objective":obj,
            "selected_on_development_only":choice,"by_stage_and_model":metrics,
            "locked_holdout_selected":metrics["heldout"][choice],
            "current_season_replay_selected":metrics["current_replay"][choice],
            "is_actual_live_forward_pilot":False,"betting_roi_tested":False}
def run(leagues=("NBA","EL")):
    successful={};errors={}
    for league in leagues:
        try:
            games,manifest=download(league)
            successful[league]=league_benchmark(games,league,manifest)
        except (SourceError,OSError,ValueError,TimeoutError) as exc:
            errors[league]=f"{type(exc).__name__}: {str(exc)[:200]}"
    return {"schema":"BASKETBOL_V1_REAL_HISTORY_RESEARCH",
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "league_results":successful,"source_errors":errors,
            "paid_data_cost_tl":0,"real_money_bets":0,
            "other_league_candidates_not_claimed_as_integrated":["EuroCup","TUR_BSL","ESP_ACB","GER_BBL","ITA_LBA","FRA_LNB","GRE_BSL","FIBA_BCL"],
            "limitations":["Historical replay only, not true out-of-sample live SHA predictions",
                "Scores and margin only; actual possessions, injury/lineup and rest are NOT in this version",
                "Third-party raw score feeds are not independently official-score-network verified",
                "No bookmaker prices, no profit or positive-EV claim",
                "EuroLeague data is noncommercial third-party statistics with separate licensing terms"]}
def mobile(x):
    lines=["# Basketbol Analiz Makinası 1.0 — gerçek geçmiş maç kabul raporu","",
           "**Araştırma amaçlı; para/odds/ROI yok.**",""]
    for league,info in x["league_results"].items():
        best=info["selected_on_development_only"]
        g=info["locked_holdout_selected"];b=info["by_stage_and_model"]["heldout"]["BASE"]
        current=info["current_season_replay_selected"]
        lines.extend([f"## {league} — test öncesi seçilen {best}",
            f"Arşivde {info['historical_game_count']} maç; ayrılmış sonraki sezon N={g['n']}.",
            f"MS doğru: {g['correct']}/{g['n']} = %{100*g['accuracy']:.2f}; Brier: {g['brier']}; logloss: {g['logloss']}",
            f"Fark MAE: {g['margin_mae']} sayı · Toplam sayı MAE: {g['total_mae']} sayı.",
            f"Basit BASE kıyası: Brier {b['brier']}, fark MAE {b['margin_mae']}, toplam MAE {b['total_mae']}.",
            f"2026-27 geriye dönük tekrar: N={current['n']} (GERÇEK ileri SHA kaydı değildir).",""])
    if x["source_errors"]:lines+=["### Kaynağı sınanamayan ligler",str(x["source_errors"])]
    lines+=["Diğer 8 aday lig henüz eklenmedi. Eksik sakatlık/kadro/tempo = tam sürüm değil.",
            "Piyasa üstünlüğü, ROI veya para kazancı gösterilmedi."]
    return "\n".join(lines)+"\n"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--mobile",required=True)
    ap.add_argument("--fail-if-empty",action="store_true")
    a=ap.parse_args();results=run()
    if a.fail_if_empty and not results["league_results"]:raise SystemExit("NO_REAL_SOURCE_ACCEPTED")
    Path(a.out).write_text(json.dumps(results,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    Path(a.mobile).write_text(mobile(results),encoding="utf-8")
    print(mobile(results))
if __name__=="__main__":main()
