"""Independent replication of frozen seven-event decision API on past and SHA.

No synthetic live seals: date-reconstructed events checked as pure math only.
Original 39 archived SHA have genuine kickoff and forecast-created clocks;
validate full API on them, without passing any outcomes to the selector.
"""
import argparse,hashlib,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"experiments/263"),str(ROOT/"research/263_independent_audit")]
from audit import GROUP,add_nov8
from audit_market_calibration import reconstruct_season
from audit_main_choice_layer import build,reconstruct_m4_lambda,LIVE_SHAPED
from audit_ranker_large_sample import attach_ids,vector
from audit_best_choice_selector import fit_2025_c3,logits_apply
from chrono_goal_decision_263 import score_markets
from chrono_goal_stage2_263 import load_predictions
from audit_full_history import EXPECTED_SHA
from shadow_primary_choice_final import (policy_load,decide,frozen_binary,MS,KG,O25)
from choice_probability_shadow_v1 import choose,with_adjusted_binary
POS=("BTTS_YES","OVER_2.5")

def check_and_eval(rows,models,policy,live=True):
    events=[];maxdiff=0.;mismatch=0
    for r in rows:
        p=vector(r,"FROZEN" if live else "RAW")
        if p is None:continue
        previous=logits_apply(p,r["base"],models)
        numbers={}
        for k in POS:
            numbers[k]=frozen_binary(p[k],r["base"][k],k,policy)
            maxdiff=max(maxdiff,abs(numbers[k]-previous[k]))
        q=with_adjusted_binary(p,numbers[POS[0]],numbers[POS[1]])
        expected=choose(previous,"SKLEARN_EXACT")
        actual=choose(q,"FROZEN_7_DECIMAL")
        mismatch+=expected["main"]!=actual["main"]
        evt=actual["main"]
        events.append((q[evt],r["obs"][evt],evt))
    if not events:return {"n":0}
    n=len(events)
    return {"n":n,"frozen_vs_exact_max_probability_abs":round(maxdiff,12),
            "selected_event_mismatch":mismatch,
            "hit_pct":round(100*sum(y for p,y,k in events)/n,3),
            "mean_pred_pct":round(100*sum(p for p,y,k in events)/n,3),
            "chosen_brier":round(sum((p-y)**2 for p,y,k in events)/n,7)}

def test_guards(policy):
    time={"forecast_created_utc":"2026-11-08T10:00:00+00:00",
          "asof_utc":"2026-11-08T10:00:00+00:00",
          "kickoff_utc":"2026-11-08T12:00:00+00:00"}
    ms={"MS1":.5,"MSX":.25,"MS2":.25}
    base={**ms,"BTTS_YES":.55,"BTTS_NO":.45,"OVER_2.5":.5,"UNDER_2.5":.5}
    c3={"BTTS_YES":.64,"BTTS_NO":.36,"OVER_2.5":.61,"UNDER_2.5":.39}
    out=decide(m4_joint_ms=ms,c3_binary=c3,league_asof=base,policy=policy,**time)
    assert out["status"]=="SHADOW_CALIBRATED_CHOICE" and out["betting_authorized"] is False
    assert abs(out["all_market_probabilities"]["BTTS_YES"]+out["all_market_probabilities"]["BTTS_NO"]-1)<1e-8
    assert abs(out["all_market_probabilities"]["OVER_2.5"]+out["all_market_probabilities"]["UNDER_2.5"]-1)<1e-8
    for name,kwargs in (
        ("AFTER_KICKOFF",{**time,"asof_utc":"2026-11-08T12:01:00+00:00"}),
        ("BEFORE_FORECAST",{**time,"asof_utc":"2026-11-08T09:00:00+00:00"}),
        ("UNQUALIFIED_TIME",{**time,"asof_utc":"2026-11-08T10:00:00"})):
        try:decide(m4_joint_ms=ms,c3_binary=c3,league_asof=base,policy=policy,**kwargs)
        except ValueError:pass
        else:raise AssertionError("GUARD_FAILED_"+name)
    no_c3=decide(m4_joint_ms=ms,c3_binary=None,league_asof=base,policy=policy,**time)
    assert no_c3["status"]=="SHADOW_PAS_NO_COMPARABLE_BINARY_MODEL"
    fb=decide(m4_joint_ms=ms,c3_binary=None,league_asof=base,
              m4_binaries_fallback=c3,policy=policy,**time)
    assert fb["status"]=="SHADOW_FALLBACK_UNCALIBRATED" and fb["research_only"]
    return {"guards_passed":7,"sample_decision":out["main_choice"],
            "sample_gap_pp":out["gap_percentage_points"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    assert hashlib.sha256(Path(args.history).read_bytes()).hexdigest()==EXPECTED_SHA
    policy=policy_load()
    guards=test_guards(policy)
    hist=reconstruct_season(args.history)
    current=load_predictions(args.predictions)
    attach_ids(current,args.predictions)
    assert (len(hist),len(current))==(2922,880)
    models,meta=fit_2025_c3(hist)
    for key in POS:
        co=policy["coefficients"][key]
        assert abs(co["intercept"]-meta[key]["intercept"])<1e-9
        assert abs(co["coefficient_c3_logit"]-meta[key]["coef"][0])<1e-9
        assert abs(co["coefficient_league_logit"]-meta[key]["coef"][1])<1e-9
    raw=check_and_eval(current,models,policy,False)
    sep_oct=[r for r in current if r["date"]>="2026-09-01"]
    lock=json.loads((ROOT/"experiments/263/model_first_selection_lock_20261120_normal_v3.json").read_text())
    lam=reconstruct_m4_lambda(args.history,{r["id"] for r in sep_oct})
    for r in sep_oct:build(r,lock["m4_joint_calibration_august"],lam[r["id"]])
    live=check_and_eval(sep_oct,models,policy)
    sealed=add_nov8()
    archive=json.loads((ROOT/"data/results_only_263/nov8_new100_terminal_archive_20261112.json").read_text())
    original=[]
    for entry in archive["rows"]:
        if entry.get("score") is None:continue
        f=json.loads((ROOT/entry["forecast_path"]).read_text())
        original.append(f)
    assert len(original)==len(sealed)==39
    for r,f in zip(sealed,original):
        g=f["model_predictions"]["M4"]["goals"]
        lam=(g["lambda_home"],g["lambda_away"])
        assert r["league"]==f["fixture"]["league"]
        assert abs(score_markets(*lam)["markets"]["1X2"]["H"]-r["p"]["M4"]["MS1"])<.000002
        build(r,lock["m4_joint_calibration_august"],lam)
    sha=check_and_eval(sealed,models,policy)
    nfull=0
    for r,f in zip(sealed,original):
        p=r["p"][LIVE_SHAPED]
        c3={k:r["p"]["C3"][k] for k in KG+O25}
        m4={k:p[k] for k in MS}
        res=decide(m4_joint_ms=m4,c3_binary=c3,league_asof=r["base"],
            forecast_created_utc=f["created_at_utc"],
            asof_utc=f["created_at_utc"],
            kickoff_utc=f["fixture"]["kickoff_utc"],policy=policy)
        assert res["status"]=="SHADOW_CALIBRATED_CHOICE"
        assert res["main_choice"]==choose(
            with_adjusted_binary(p,
                frozen_binary(c3["BTTS_YES"],r["base"]["BTTS_YES"],"BTTS_YES",policy),
                frozen_binary(c3["OVER_2.5"],r["base"]["OVER_2.5"],"OVER_2.5",policy)),
            "DIRECT")["main"]
        nfull+=1
    assert nfull==39
    for label,v,expected in (("raw",raw,873),("live",live,615),("sealed",sha,39)):
        assert v["n"]==expected and v["selected_event_mismatch"]==0,(label,v)
        assert v["frozen_vs_exact_max_probability_abs"]<1e-6,(label,v)
    result={
        "schema":"263_FROZEN_SHADOW_PRIMARY_DECISION_REPLICATION_V1",
        "original_sha256":EXPECTED_SHA,
        "frozen_policy":policy["schema"],
        "source_train_season":policy["training_year"],
        "guards":guards,
        "model_coefficients_verified_same_2025_training":True,
        "coefficient_rounding_exact_selection_match":True,
        "source_counts":{"history_asof":len(hist),"2026_asof":len(current),"live_joint_ms":len(sep_oct),
                         "sha_real_prematch":nfull},
        "metrics":{"2026_aug_oct_raw_ms":raw,"2026_sep_oct_joint_ms":live,"2026_nov8_real_sha":sha},
        "production_modified":False,
        "betting_authorized":False,
        "no_hidden_future_scores_supplied_to_decide":True,
        "no_asof_history_mislabeled_as_sha":True,
    }
    out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    (out/"21_frozen_shadow_validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n")
    report="# 2.6.3 ana tercih: dondurulmuş çalışır aday kontrolü\n\n"
    report+="Ana 2.6.3 değişmedi. Gölge karar modülü M4 Ağustos ortak MS ile C3 KG ve 2.5 için 2025/26 sezonuna göre öğrenilmiş sabit lojistik olasılık kullanır.\n\n"
    report+="| Dönem | N | İsabet | Ortalama tahmin | Seçim Brier | Pure/sklearn farklı ana olay |\n|---|---:|---:|---:|---:|---:|\n"
    for n,m in result["metrics"].items():
        report+=f"| {n} | {m['n']} | %{m['hit_pct']} | %{m['mean_pred_pct']} | {m['chosen_brier']} | {m['selected_event_mismatch']} |\n"
    report+="\n39 gerçek SHA üzerinde orijinal forecast/KO zamanlarıyla tam arayüz çalıştırıldı. Yanlış saat, eksik veri ve family normalization kontrolleri olumlu. Bu sonuçlar araştırmada daha önce görülmüş geçmiş veriyi tamamen bağımsız kör doğrulama yapmaz. Canlı üretim değişmedi.\n"
    (out/"22_frozen_shadow_validation_report.md").write_text(report,encoding="utf-8")
    print("FROZEN_SHADOW_REPLICATION="+json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
