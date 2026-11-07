"""7 Nov 2026 scope review of all 44 pinned candidate fixtures, READ-ONLY.

Only the 18 already externally verified official candidate names are rechecked
through the live official identity gate and original B/C2/C3/M4 pipeline. No
new100 pilot record, bookmaker API call, history mutation or Git push.
Temporary workspace forward_morning_263 files are discarded by CI runner.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from sabah_batch_263 import named,run,save_new,sha
from market_fifth_baseline_263 import sealed_payload
from forward_c3 import read_aware

DAY="2026-11-07"
COHORT="READONLY_TODAY_SCOPE_NOT_NEW100_PILOT"
PINNED="experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json"
HISTORY="data/quad_accepted_263/extended_history.csv"
BASE="m4_quad_base/historical_results.csv"
ACCEPTANCE="data/quad_accepted_263/source_acceptance.json"
LOCK="experiments/263/m4_lock.json"
TR=ZoneInfo("Europe/Istanbul")
SELECTED=[
 ("TUR1","Eyüpspor","Kocaelispor"),
 ("TUR1","Samsunspor","Konyaspor"),
 ("TUR1","Galatasaray","Amed SK"),
 ("ENG1","Leeds United","Tottenham Hotspur"),
 ("ENG1","Arsenal","Hull City"),
 ("ENG1","Fulham","Newcastle United"),
 ("ENG1","Nottingham Forest","Manchester City"),
 ("ESP1","Osasuna","Athletic Club"),
 ("ESP1","Valencia","Real Madrid"),
 ("ITA1","Cagliari","Frosinone"),
 ("ITA1","Torino","Lecce"),
 ("ITA1","Parma","Bologna"),
 ("ITA1","Roma","Sassuolo"),
 ("FRA1","Auxerre","Paris FC"),
 ("FRA1","Paris Saint-Germain","Troyes"),
 ("NED1","Fortuna Sittard","Telstar"),
 ("NED1","ADO Den Haag","Sparta Rotterdam"),
 ("NED1","Excelsior","Go Ahead Eagles")]
PREVIOUS={
 ("TUR1","Samsunspor","Konyaspor"):"5b643f0abf6a49abff90b1ac",
 ("ENG1","Arsenal","Hull City"):"ffdea2ac0f8f1c80ccbac76c",
 ("ESP1","Valencia","Real Madrid"):"b7fc2db793df14715edee615"}
MARKETS=("MS1","MSX","MS2","BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def digest(x):return sha({k:v for k,v in x.items() if k!="payload_sha256"})
def summarize(f,d,origin):
    sealed_payload(f,"quad_forward_263_v1")
    sealed_payload(d,"263_four_model_value_decision_research_v1")
    if d.get("forecast_sha256")!=f["payload_sha256"]:
        raise ValueError("DECISION_NOT_LINKED_TO_FORECAST")
    ms=[];others={}
    for r in d.get("all_market_diagnostics",[]):
        market=r.get("market")
        if market in MARKETS:
            others[market]={"p":r.get("calibrated_probability"),
                "anchor":r.get("anchor_model"),"support":r.get("support_count"),
                "qualifications":r.get("qualification_reasons",[])}
            if market in ("MS1","MSX","MS2") and isinstance(r.get("calibrated_probability"),(int,float)):
                ms.append((r["calibrated_probability"],market))
    models={}
    for name in ("B","C2","C3","M4"):
        m=f["model_predictions"][name]
        if m.get("status")!="AVAILABLE":
            models[name]={"status":m.get("status"),"reason":m.get("reason")}
        else:
            p=m["goals"]["markets"]
            models[name]={"status":"AVAILABLE","MS1":p["1X2"]["H"],
                "MSX":p["1X2"]["D"],"MS2":p["1X2"]["A"],
                "KG_VAR":p["BTTS_YES"],"UST_1_5":p["OVER_1.5"],
                "UST_2_5":p["OVER_2.5"],"UST_3_5":p["OVER_3.5"]}
    return {"status":"EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE",
        "source":origin,"fixture":f["fixture"],
        "forecast_sha256":f["payload_sha256"],
        "decision_sha256":d["payload_sha256"],
        "models":models,
        "calibrated_market_probabilities":others,
        "descriptive_top_calibrated_MS_market":
           {"market":max(ms)[1],"p":max(ms)[0]} if ms else None,
        "decision_status":d["status"],
        "verified_bookmaker_odds":False,
        "betting_authorized":False}

def run_today():
    utc=datetime.now(timezone.utc);now=utc.astimezone(TR)
    if now.date().isoformat()!=DAY or not 5<=now.hour<13:
        raise ValueError("READONLY_DATED_MORNING_EXECUTION_ONLY")
    all_candidates=named("legacy96",DAY,PINNED)
    triples={(r["league"],r["home"],r["away"]) for r in all_candidates}
    if len(all_candidates)!=44 or len(triples)!=44 or len(SELECTED)!=18 or not set(SELECTED).issubset(triples):
        raise ValueError("PINNED_44_SOURCE_OR_SELECTED_18_CHANGED")
    actual=[{"league":l,"home":h,"away":a} for l,h,a in SELECTED if (l,h,a) not in PREVIOUS]
    manifest=Path("/tmp/263_20261107_scoped_15_readonly.json")
    manifest.write_text(json.dumps({"schema":"SABAH_TOPLU_V1","day_turkey":DAY,
                                    "matches":actual},ensure_ascii=False),encoding="utf-8")
    report=run("new100",DAY,manifest,HISTORY,BASE,ACCEPTANCE,LOCK)
    if report["odds_api_calls"]!=0 or report["betting_authorized"] is not False:
        raise ValueError("BOOKMAKER_OR_BETTING_FORBIDDEN")
    bykey={(r["league"],r["home"],r["away"]):r for r in report["outcomes"]}
    rows=[]
    for league,home,away in SELECTED:
        key=(league,home,away)
        if key in PREVIOUS:
            stem=PREVIOUS[key]
            path=Path("forward_acceptance_263")/DAY/(stem+".json")
            f=read(path)
            d=read(Path("experiments/263/sabah_research/acceptance3")/DAY/stem/"decision.json")
            record=summarize(f,d,"EXISTING_SEALED_ACCEPTANCE3_NOT_NEW100")
        else:
            item=bykey[key]
            if item["status"]=="REGISTERED_FOUR_MODELS_EXPERIMENTAL":
                f=read(item["forecast_path"])
                path=Path(item["forecast_path"]);stem=path.stem
                d=read(Path("experiments/263/sabah_research/new100")/DAY/stem/"decision.json")
                record=summarize(f,d,"TEMPORARY_NONPILOT_FRESH_COMPUTATION")
            else:
                record={"status":item["status"],
                        "reason":item.get("reason","unverified"),"source":"LIVE_OFFICIAL_RECHECK_FAILED"}
        rows.append({"league":league,"home":home,"away":away,**record})
    failed=[x for x in all_candidates if (x["league"],x["home"],x["away"]) not in set(SELECTED)]
    return {
      "schema":"263_NOV07_ALL_10_LEAGUES_READONLY_REVIEW_V1",
      "observed_at_utc":utc.isoformat(),"day_turkey":DAY,
      "scope_leagues":sorted({r["league"] for r in all_candidates}),
      "pinned_daily_candidates":len(all_candidates),
      "prior_official_named_gate_evidence_count":18,
      "not_officially_reverified_in_this_run":len(failed),
      "other_26_candidates":failed,
      "selected_18":rows,
      "new_temporary_model_outputs":sum(x["source"]=="TEMPORARY_NONPILOT_FRESH_COMPUTATION"
                                        for x in rows),
      "reused_sealed_engineering_records":3,
      "new100_git_pilot_records_written":0,
      "bookmaker_api_calls":0,"official_betting_selections":0,
      "limitations":["Previous 18 source gates are rechecked by the live official gateway",
       "26 date-candidate fixtures still lack live official gating in this review",
       "Temporary forecasts are not pilot records and must never be backdated",
       "No synchronized bookmaker odds therefore all decisions RESEARCH_PAS",
       "Model availability and calibrated market anchors vary by fixture",
       "First XI unavailable for many fixtures at morning review",
       "No claim of model superiority based on these predictions"]}

def render(data):
    lines=["# 7 Kasım 2026 | 10 lig — MAKİNA 2.6.3",
           "","**Salt okunur sabah saha taraması:** "+
           str(data["pinned_daily_candidates"])+" aday; 18 önceki resmî kaynak eşleşmesi.",
           "**Yeni100 pilot kaydı:** 0; **oran API çağrısı:** 0; **kesin bahis tercihi:** YOK.","",
           "| Lig | Maç | TSİ başlama | MS yön (kalibre, tek pazar) | B/C2/C3/M4 | Durum |",
           "|---|---|---:|---:|---|---|"]
    for r in data["selected_18"]:
        if r["status"]=="EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE":
            kickoff=read_aware(r["fixture"]["kickoff_utc"]).astimezone(TR).strftime("%H:%M")
            ms=r["descriptive_top_calibrated_MS_market"]
            p=("—" if ms is None else ms["market"]+" "+("%.1f%%"%(100*ms["p"])).replace(".",","))
            models="/".join("✓" if r["models"][m]["status"]=="AVAILABLE" else "—"
                            for m in ("B","C2","C3","M4"))
            status="PAS (oran yok)"
        else: kickoff="—";p="—";models="—";status=r["status"]+": "+r.get("reason","")
        lines.append("| "+r["league"]+" | "+r["home"]+" – "+r["away"]+" | "+kickoff+
                     " | "+p+" | "+models+" | "+status+" |")
    lines+=["","**Doğrulama engeli olan diğer 26 aday:**"]
    from collections import Counter
    counts=Counter(x["league"] for x in data["other_26_candidates"])
    for league,n in sorted(counts.items()):lines.append("- "+league+": "+str(n))
    lines+=["","Kaynak uyarısı: Kalibre edilen tekli MS pazar olasılıkları kendi başına "+
            "tam normalize bir 1-X-2 dağılımı değildir. KG ve gol çizgilerinin ham "+
            "B/C2/C3/M4 yüzdeleri JSON raporunda ayrı ayrı bulunur.",
            "Bunlar bahis önerisi değildir; oran ve EV hesaplanmadı."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    p.add_argument("--mobile",required=True);a=p.parse_args()
    data=run_today()
    save_new(a.out,data);save_new(a.mobile,render(data))
    print(json.dumps({"candidates":data["pinned_daily_candidates"],
        "prior_official_verified":data["prior_official_named_gate_evidence_count"],
        "temporary_new_models":data["new_temporary_model_outputs"],
        "saved_engineering_models":data["reused_sealed_engineering_records"],
        "new100_git_pilot_records":0,
        "missing":len(data["other_26_candidates"]),
        "bookmaker_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
