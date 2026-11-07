"""Read-only late-window all-44 2026-11-07 analyses; retains every candidate.

Official live-page + canonical gate before any model, user supplied frozen list
not Module0. Every newly calculated experimental forecast is confined to
TemporaryDirectory and deleted before the GitHub job ends. No pilot/odds.
"""
from __future__ import annotations
import argparse,json,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from collections import Counter
from zoneinfo import ZoneInfo
from sabah_batch_263 import named,sha
from sabah_named_source_acceptance_263 import named_only_runner
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from forward_c3 import valid_gate,read_aware
from market_fifth_baseline_263 import sealed_payload
from sabah_today_scope_readonly_263 import summarize,PREVIOUS

DAY="2026-11-07"
FROZEN="experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json"
HISTORY="data/quad_accepted_263/extended_history.csv"
BASE="m4_quad_base/historical_results.csv"
AUDIT="data/quad_accepted_263/source_acceptance.json"
M4LOCK="experiments/263/m4_lock.json"
DEV="experiments/263/forward_dev_calibration_lock_263.json"
TR=ZoneInfo("Europe/Istanbul")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))

def one_day():
    now=datetime.now(timezone.utc)
    if now.astimezone(TR).date().isoformat()!=DAY:raise ValueError("NO_POSTDATED_DAY_RESEARCH")
    candidates=named("legacy96",DAY,FROZEN)
    if len(candidates)!=44:raise ValueError("44_IMMUTABLE_NAMES_REQUIRED")
    gateway=OfficialFixtureGateway(gate_runner=named_only_runner)
    from forward_quad import predict_quad_from_verified_gate
    from forward_empirical_baseline_263 import produce
    from four_model_value_policy_263 import decide
    dev=read(DEV)
    result=[]
    with tempfile.TemporaryDirectory(prefix="263_44_nonpilot_") as scratch:
        outdir=Path(scratch)
        for r in candidates:
            league,home,away=r["league"],r["home"],r["away"]
            item={"league":league,"home":home,"away":away,
                  "status":"PENDING_OFFICIAL_SOURCE","source":"NO_PILOT_WRITE"}
            try:
                gate=gateway.lookup(league,home,away)
                evidence=gateway.latest_match_evidence(league,home,away)
                item["gate_evidence"]=evidence
                if not isinstance(gate,dict) or gate.get("status")!="VERIFIED":
                    item["status"]="BLOCKED_OFFICIAL_PAGE_OR_CANONICAL_ID"
                    item["reason"]=gate.get("reason") if isinstance(gate,dict) else "INVALID_GATE"
                    result.append(item);continue
                checked=datetime.now(timezone.utc)
                _,_,_,ko,_,_=valid_gate(gate,checked)
                item["official_kickoff_utc"]=ko.isoformat()
                item["official_source_url"]=gate.get("source_url")
                if ko.astimezone(TR).date().isoformat()!=DAY:
                    item["status"]="BLOCKED_OFFICIAL_DAY_NOT_TODAY"
                    result.append(item);continue
                if checked+timedelta(minutes=2)>=ko:
                    item["status"]="BLOCKED_KICKOFF_TOO_CLOSE_OR_PAST"
                    result.append(item);continue
                key=(league,home,away)
                if key in PREVIOUS:
                    stem=PREVIOUS[key]
                    f=read(Path("forward_acceptance_263")/DAY/(stem+".json"))
                    d=read(Path("experiments/263/sabah_research/acceptance3")/DAY/stem/"decision.json")
                    record=summarize(f,d,"EXISTING_SEALED_3MATCH_ENGINEERING_NOT_NEW100")
                else:
                    path,f=predict_quad_from_verified_gate(
                        gate,HISTORY,outdir,M4LOCK,now=checked,
                        base=BASE,source_audit=AUDIT)
                    sealed_payload(f,"quad_forward_263_v1")
                    b=produce(f,HISTORY,now=checked)
                    d=decide(f,b,dev,observation=None,now=checked)
                    if d["status"]!="RESEARCH_PAS":
                        raise ValueError("NO_ODDS_MUST_BE_RESEARCH_PAS")
                    record=summarize(f,d,"READONLY_TEMPORARY_MODEL_DELETED_AFTER_JOB")
                if record.get("decision_status")!="RESEARCH_PAS":
                    raise ValueError("DECISION_NOT_PAS")
                item.update(record)
            except (ValueError,TypeError,KeyError,OSError,AssertionError) as err:
                item["status"]="BLOCKED_DATA_OR_MODEL" if item.get("official_kickoff_utc") else "BLOCKED_OFFICIAL_SOURCE"
                item["reason"]=type(err).__name__+":"+str(err)[:160]
            result.append(item)
    grouped=Counter(x["status"] for x in result)
    return {"schema":"263_ALL_44_NOV7_NONPILOT_RESEARCH_V1",
        "day_turkey":DAY,"as_of_utc":now.isoformat(),
        "pinned_candidates":len(candidates),"all_candidates_preserved":True,
        "statuses":dict(grouped),
        "new_real_pilot_100_forecasts":0,
        "odds_or_bookmaker_calls":0,
        "permanently_saved_model_records":0,
        "source_policy":"ONLY_LIVE_OFFICIAL_PAGE_CANONICAL_GATE_NO_OLD_FALLBACK",
        "research_only":True,"items":result,
        "source_coverage":gateway.coverage()}

def render(r):
    lines=["# 7 Kasım 2026 — 44 maçın tamamı, Makina 2.6.3",
           "","**44 adayın hiçbirini listeden çıkarmadık.**",
           "**Yeni 100 pilot kaydı:** 0; **oran API çağrısı:** 0.",
           "","| Lig | Karşılaşma | TSİ | Kalibre MS yönü | B/C2/C3/M4 | Durum |",
           "|---|---|---:|---:|---|---|"]
    for x in r["items"]:
        if x["status"]=="EXPERIMENTAL_MODEL_OUTPUT_AVAILABLE":
            ko=read_aware(x["fixture"]["kickoff_utc"]).astimezone(TR).strftime("%H:%M")
            ms=x.get("descriptive_top_calibrated_MS_market")
            value=(ms["market"]+" "+f'{ms["p"]*100:.1f}%' if ms else "—")
            models="/".join("✓" if x["models"][m]["status"]=="AVAILABLE" else "—"
                              for m in ("B","C2","C3","M4"))
            st="RESEARCH_PAS · oran yok"
        else:
            ko=read_aware(x["official_kickoff_utc"]).astimezone(TR).strftime("%H:%M") if x.get("official_kickoff_utc") else "?"
            models="—";value="—";st=x["status"]+" · "+x.get("reason","")
        lines.append("| "+x["league"]+" | "+x["home"]+" – "+x["away"]+" | "+ko+
                     " | "+value+" | "+models+" | "+st.replace("|","/")+" |")
    lines+=["","### Sonuç",str(r["statuses"]),"",
        "**Yorum:** Resmî fikstür bulmak modelin çalışması anlamına gelmez. "
        "EFL/Portekiz/Belçika'nın güncel resmî web sayfaları insan tarafından "
        "bulundu, ancak bu betik otomatik olarak ayrıştırılabilen resmî "
        "sayfa kanıtını ister. Bağımsız otomatik kanıt olmadan pilot tahmini yok.",
        "MS tek-pazar kalibrasyon olasılıkları normalize 1X2 toplamı değildir.",
        "Bütün maçlar yalnız araştırma amaçlı; oran yoksa PAS."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    p.add_argument("--mobile",required=True);a=p.parse_args()
    x=one_day()
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:json.dump(x,f,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False);f.write("\n")
    md=Path(a.mobile);md.parent.mkdir(parents=True,exist_ok=True)
    with md.open("x",encoding="utf-8") as f:f.write(render(x))
    print(json.dumps({"total":x["pinned_candidates"],"statuses":x["statuses"],
                      "new100_added":0,"odds_calls":0},ensure_ascii=False))
if __name__=="__main__":main()
