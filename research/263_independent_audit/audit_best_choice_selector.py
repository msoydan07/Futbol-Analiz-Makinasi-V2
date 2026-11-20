"""Evidence-driven 263 primary event selector: prequential original history.

Never uses 2025 calibration of M4 MS for 2026 Aug or 2025 (version guard).
Uses original frozen August M4 joint MS in Sep/Oct and 39 November SHA.
Only fits C3 KG/O25 from previous 2025/26, sequentially updates as-of C3
using entire 2025/26 and 2026 Aug-Oct historic results known before the date.
NO new production release, odds, xG, money or extra pilot.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"experiments/263"),str(ROOT/"research/263_independent_audit")]
import numpy as np
from sklearn.linear_model import LogisticRegression
from audit import GROUP,SEVEN,add_nov8
from audit_market_calibration import reconstruct_season
from audit_main_choice_layer import build,reconstruct_m4_lambda,LIVE_SHAPED
from audit_ranker_large_sample import attach_ids,vector
from chrono_goal_decision_263 import score_markets
from chrono_goal_stage2_263 import load_predictions
from audit_full_history import EXPECTED_SHA
from choice_probability_shadow_v1 import (HistoricalC3Index,assert_vector,
    shrink_binary,with_adjusted_binary,mix_binary,choose)

CANDIDATES=("RAW","C3_25_BASE_75","C3_50_BASE_50",
            "C3_BETA80_N30","C3_BETA200_N30",
            "C3_LOGIT_2025_ONLY","C3_BLEND_25_BETA80",
            "C3_BLEND_25_LOGIT2025")
SEED=26320261120
POS=("BTTS_YES","OVER_2.5")

def logit(x):
    x=min(.9999,max(.0001,float(x)))
    return math.log(x/(1-x))

def fit_2025_c3(data):
    train=[r for r in data if "C3" in r["p"]]
    assert len(train)>2200
    models={};meta={}
    for key in POS:
        x=np.asarray([[logit(r["p"]["C3"][key]),logit(r["base"][key])]
                      for r in train])
        y=np.asarray([int(r["obs"][key]) for r in train])
        model=LogisticRegression(C=.5,max_iter=500,random_state=SEED%(2**32))
        model.fit(x,y)
        models[key]=model
        meta[key]={"n":len(train),"coef":[round(float(v),7) for v in model.coef_[0]],
                   "intercept":round(float(model.intercept_[0]),7),
                   "positive_rate":round(float(y.mean()),6)}
    return models,meta

def logits_apply(p,base,models):
    vals={}
    for key in POS:
        x=np.asarray([[logit(p[key]),logit(base[key])]])
        vals[key]=float(models[key].predict_proba(x)[0, list(models[key].classes_).index(1)])
    return with_adjusted_binary(p,vals[POS[0]],vals[POS[1]])

def make_candidates(row,idx,models,mode):
    p=vector(row,mode)
    if p is None:return None
    b=row["base"]
    assert_vector(p)
    sh25=shrink_binary(p,b,.25)
    q={}
    for key in POS:
        q[key],cnt=idx.estimate(key,row["p"]["C3"][key],prior=80,min_n=30)
    b80=with_adjusted_binary(p,q[POS[0]],q[POS[1]])
    q={}
    for key in POS:
        q[key],cnt=idx.estimate(key,row["p"]["C3"][key],prior=200,min_n=30)
    b200=with_adjusted_binary(p,q[POS[0]],q[POS[1]])
    l=logits_apply(p,b,models)
    result={
        "RAW":p,
        "C3_25_BASE_75":sh25,
        "C3_50_BASE_50":shrink_binary(p,b,.5),
        "C3_BETA80_N30":b80,
        "C3_BETA200_N30":b200,
        "C3_LOGIT_2025_ONLY":l,
        "C3_BLEND_25_BETA80":mix_binary(sh25,b80,.5),
        "C3_BLEND_25_LOGIT2025":mix_binary(sh25,l,.5),
    }
    for val in result.values():assert_vector(val)
    return result

def by_day(data):
    groups=collections.defaultdict(list)
    for r in data:groups[r["date"]].append(r)
    return [(date,groups[date]) for date in sorted(groups)]

def audit(train,targets,models,mode):
    # Training observations are always earlier than every evaluation date.
    assert max(r["date"] for r in train)<min(r["date"] for r in targets)
    index=HistoricalC3Index()
    for date,rows in by_day(train):
        index.add_batch(rows)
    records=[]
    for date,rows in by_day(targets):
        today=[]
        for r in rows:
            variants=make_candidates(r,index,models,mode)
            if variants is None:continue
            decisions={}
            for name,p in variants.items():
                info=choose(p,name);ev=info["main"]
                decisions[name]={
                    **info,
                    "family":next(f for f,keys in GROUP.items() if ev in keys),
                    "actual":int(r["obs"][ev]),
                    "selected_loss":(p[ev]-r["obs"][ev])**2,
                    "full_market_brier":{
                        "MS":sum((p[k]-r["obs"][k])**2 for k in GROUP["MS"]),
                        "KG":(p["BTTS_YES"]-r["obs"]["BTTS_YES"])**2,
                        "O25":(p["OVER_2.5"]-r["obs"]["OVER_2.5"])**2,
                    },
                }
            records.append({"date":date,"league":r["league"],"id":r["id"],
                            "decisions":decisions})
            today.append(r)
        # Update only after all choices for the day, across all leagues.
        index.add_batch(rows)
    return records

def summarize(rows):
    d={}
    for name in CANDIDATES:
        r=[x["decisions"][name] for x in rows]
        n=len(r)
        if n==0:d[name]={"n":0};continue
        total=sum(x["actual"] for x in r)
        d[name]={
            "n":n,"hits":total,"hit_pct":round(100*total/n,3),
            "pred_mean_pct":round(100*sum(x["main_probability"] for x in r)/n,3),
            "chosen_brier":round(sum(x["selected_loss"] for x in r)/n,7),
            "MS_brier":round(sum(x["full_market_brier"]["MS"] for x in r)/n,7),
            "KG_brier":round(sum(x["full_market_brier"]["KG"] for x in r)/n,7),
            "O25_brier":round(sum(x["full_market_brier"]["O25"] for x in r)/n,7),
            "close_2pp_pct":round(100*sum(x["near_tie"] for x in r)/n,2),
            "family_counts":dict(sorted(collections.Counter(x["family"] for x in r).items())),
            "event_counts":dict(sorted(collections.Counter(x["main"] for x in r).items())),
            "p_atleast_65_n":sum(x["main_probability"]>=.65 for x in r),
            "p_atleast_65_hit_pct":(
                round(100*sum(x["actual"] for x in r if x["main_probability"]>=.65)
                      /sum(x["main_probability"]>=.65 for x in r),2)
                if any(x["main_probability"]>=.65 for x in r) else None),
        }
    return d

def paired(rows,name,compare="RAW",iterations=900):
    by=collections.defaultdict(list)
    changes=collections.Counter()
    for row in rows:
        a=row["decisions"][name];b=row["decisions"][compare]
        changes["different_event" if a["main"]!=b["main"] else "same_event"]+=1
        changes["different_family" if a["family"]!=b["family"] else "same_family"]+=1
        by[row["date"]].append((a["actual"]-b["actual"],
                                 b["selected_loss"]-a["selected_loss"]))
    if not by:return {"n":0}
    allv=[v for arr in by.values() for v in arr]
    n=len(allv)
    obj={"n":n,"days":len(by),
         "hit_delta_pp":round(100*sum(v[0] for v in allv)/n,4),
         "chosen_brier_gain":round(sum(v[1] for v in allv)/n,8),
         "flips":dict(changes)}
    if len(by)>=4:
        rng=random.Random(SEED)
        days=sorted(by)
        res=[[],[]]
        for _ in range(iterations):
            sample=[v for dt in days for v in by[rng.choice(days)]]
            res[0].append(100*sum(v[0] for v in sample)/len(sample))
            res[1].append(sum(v[1] for v in sample)/len(sample))
        for s in res:s.sort()
        obj["hit_ci95_pp"]=[round(res[0][int(.025*iterations)],3),
                             round(res[0][int(.975*iterations)],3)]
        obj["brier_gain_ci95"]=[round(res[1][int(.025*iterations)],8),
                                round(res[1][int(.975*iterations)],8)]
    return obj

def report(d):
    lines=["# 2.6.3 — Tek ana tercihi mühendisçe seçmek: tarih-kilitli model kararı","",
        "Bu rapor sonuçları kendiliğinden canlıya terfi ettirmez. Sadece izole araştırma kodu çalıştırıldı.",
        "Temel hedef: MS1, X, MS2, KG Var/Yok, 2.5 Üst/Alt olasılıklarını **aynı ölçekte kalibre edip** maç başına sadece en büyük olasılıklı olayı ana tercih yapmak.",
        "Olayın gerçek olasılığı bilinemez; kaçınılmaz belirsizliğin bir kısmı açıklanmalıdır.",
        "",
        "## Veri ayrımı ve güvenlik","",
        "- Orijinal 4.413 maç kaynağı SHA sabit; 2025/26 2.922 maçın C3 geçmişi, 2026/27 Ağustos-Ekim 880 tarih öncesi retrospektif rekonstrüksiyon, 8 Kasım 39 gerçek SHA.",
        "- 2025/26 C3 KG/2.5 bağımsız olarak her pazar için sadece *önceden* öğrenildi (lojistik); geçmiş tahmin ve sonuçlar 2026 testinden önce tamamlanmıştı.",
        "- Beta kalibratörü her maç günü sadece önceki günlerin C3 olasılık/sonuçlarını kullanır; **aynı günün sonuçları yok**.",
        "- Canlıya yakın MS: Ağustos 2026'da kilitli ortak M4 MS kalibrasyonu sadece 2026 Eylül-Ekim ve Nov8 mühürlerinde kullanıldı; 2025/26 ve Ağustos 2026'ya yanlış uygulanmadı.",
        "- 2025/26 M4 hiperparametre geliştirme, 2026/27 önceden araştırılan dönem. Sonuçlar yeni, tamamen kör dış test değildir.",
        "",
        "## Karşılaştırılan sabit seçenekler","",
        "- RAW: M4 MS + C3 KG ve 2.5 ham yüzdeleri.",
        "- C3_25_BASE_75, C3_50_BASE_50: KG ve 2.5 için ham C3 ve o günün öncesindeki lig bazını karıştır, MS aynen.",
        "- C3_BETA80_N30, C3_BETA200_N30: aynı marketin ±5pp yakın geçmişini 80 veya 200 örneklik model yüzdesi öncülüyle yumuşat; n<30 ise C3 hamına dön.",
        "- C3_LOGIT_2025_ONLY: 2025/26 sezonunda C3 ve yalnız geçmiş lig bazını kullanarak öğrenilmiş ayrı KG/2.5 L2 lojistik kalibratör.",
        "- C3_BLEND_25_BETA80 ve C3_BLEND_25_LOGIT2025: %25 C3-lig karışımını diğer kalibratörle 50/50 birleştir, MS aynen.",
        "",
        "## Günlere göre sınırları koruyan sonuçlar",""]
    for period,v in d["periods"].items():
        lines += [f"### {period} — {v['n']} maç, {v['days']} takvim günü","",
            "| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |",
            "|---|---:|---:|---:|---:|---:|---:|"]
        for name in CANDIDATES:
            x=v["metrics"][name]
            lines.append(f"| {name} | {x['n']} | {x.get('hit_pct')} | {x.get('pred_mean_pct')} | {x.get('chosen_brier')} | {x.get('KG_brier')} | {x.get('O25_brier')} |")
        lines.append("")
    lines += ["## Sorumlu kullanım kararı","",
              "En yüksek geçmiş isabet tek başına yetmez: aynı maçlarda eşleşmiş fark, gün-blok %95 aralık ve öngörülen yüzde-gerçekleşen oran uyumu birlikte değerlendirilir.",
              "İlk iki olasılık arasında <=2 yüzde puanı varsa kesin üstünlük gibi gösterilmez; **YAKIN ADAYLAR** etiketiyle ikinci aday açıklanır. Otomatik PAS değildir.",
              "Yeterli veri olmadığında model çıkışının olasılık doğruluğu garanti edilmez; veri olmadığı için başarı oranı uydurulmaz.",
              "Önceki tekrar testleri nedeniyle sahte şekilde büyük sayıda bağımsız canlı mühür iddiası yoktur; 39 gerçek SHA tek gün.",
              "Ana üretim kodu, günlük mühürler, xG sorunu, PDF, maç önü odds, iddaa ve otomasyonlar değiştirilmedi.",
              "Detaylı ham JSON ve tüm paired bootstrap: 18_candidate_selector_result.json; kod: audit_best_choice_selector.py; bağımsız seçim API: choice_probability_shadow_v1.py.",
              ""]
    return "\n".join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    assert hashlib.sha256(Path(a.history).read_bytes()).hexdigest()==EXPECTED_SHA
    history=reconstruct_season(a.history)
    eval26=load_predictions(a.predictions)
    attach_ids(eval26,a.predictions)
    assert len(history)==2922 and len(eval26)==880
    models,meta=fit_2025_c3(history)
    # 2026 original raw version: full 880, with 2025 training C3 before it.
    raw=audit(history,eval26,models,"RAW")
    # Frozen August M4 joint MS available *from September onwards*.
    august=[r for r in eval26 if r["date"]<"2026-09-01"]
    current=[r for r in eval26 if r["date"]>="2026-09-01"]
    lock=json.loads((ROOT/"experiments/263/model_first_selection_lock_20261120_normal_v3.json").read_text())
    f4=reconstruct_m4_lambda(a.history,{r["id"] for r in current})
    for r in current:build(r,lock["m4_joint_calibration_august"],f4[r["id"]])
    sealed=add_nov8()
    archive=json.loads((ROOT/"data/results_only_263/nov8_new100_terminal_archive_20261112.json").read_text())
    sdata=[]
    for entry in archive["rows"]:
        if entry.get("score") is None:continue
        f=json.loads((ROOT/entry["forecast_path"]).read_text())
        g=f["model_predictions"]["M4"]["goals"]
        sdata.append((f["payload_sha256"],f,(g["lambda_home"],g["lambda_away"])))
    assert len(sealed)==len(sdata)==39
    for r,(sha,f,lam) in zip(sealed,sdata):
        assert r["league"]==f["fixture"]["league"]
        assert abs(score_markets(*lam)["markets"]["1X2"]["H"]-r["p"]["M4"]["MS1"])<.000002
        r["id"]=sha
        build(r,lock["m4_joint_calibration_august"],lam)
    assert len(set(r["id"] for r in history+eval26+sealed))==3841
    live=audit(history+august,current+sealed,models,"FROZEN")
    target={
        "2026_aug_oct_880_raw_M4":raw,
        "2026_aug_sep_587_raw_M4":[r for r in raw if r["date"]<"2026-10-01"],
        "2026_oct_293_raw_M4":[r for r in raw if r["date"]>="2026-10-01"],
        "2026_sep_oct_621_frozen_MS":[r for r in live if r["date"]<"2026-11-01"],
        "2026_oct_293_frozen_MS":[r for r in live if r["date"][:7]=="2026-10"],
        "2026_nov8_39_original_sha":[r for r in live if r["date"][:7]=="2026-11"],
        "2026_sep_oct_nov_660_frozen_MS":live,
    }
    assert [len(x) for x in target.values()]==[873,580,293,615,293,39,654]
    result={
        "schema":"263_FREEZE_2025_C3_CALIBRATION_AND_DATEWISE_CHOICE_V1",
        "original_sha256":EXPECTED_SHA,
        "status":"EXPLORE_SHADOW_ONLY_NOT_BLIND",
        "source_counts":{"history_2025":2922,"asof_2026":880,"original_nov8_sha":39,
                         "raw_comparable":873,"frozen_joint_MS_sep_oct":615,
                         "frozen_joint_MS_sep_oct_nov":654},
        "models_2025_fit_meta":meta,
        "candidates":list(CANDIDATES),
        "no_2026_training_for_logistic":True,
        "beta_updates_after_every_complete_calendar_day":True,
        "ms_versions_not_crossed":True,
        "nov8_true_prekickoff_sha_only_one_day":True,
        "repeated_research_not_independent_holdout":True,
        "active_model_changed":False,
        "odds_used":False,"xg_used":False,"betting_authorized":False,
        "periods":{period:{"n":len(rows),"days":len(set(r["date"] for r in rows)),
                            "metrics":summarize(rows),
                            "paired_vs_raw":{k:paired(rows,k) for k in CANDIDATES if k!="RAW"}}
                   for period,rows in target.items()},
    }
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    (out/"18_candidate_selector_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (out/"19_candidate_selector_report.md").write_text(report(result),encoding="utf-8")
    print("C3_SELECTOR_SUMMARY="+json.dumps({
        "n":result["source_counts"],"coef":meta,
        "periods":{period:{k:{"hit":v["hit_pct"],"pred":v["pred_mean_pct"],
                      "single_brier":v["chosen_brier"],"kg":v["KG_brier"],"o25":v["O25_brier"],
                      "delta":x["paired_vs_raw"].get(k,{}).get("hit_delta_pp")}
                      for k,v in x["metrics"].items()}
                   for period,x in result["periods"].items()}},
        sort_keys=True,ensure_ascii=False))

if __name__=="__main__":main()
