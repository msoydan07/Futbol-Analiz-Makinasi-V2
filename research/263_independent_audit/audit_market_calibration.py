"""Calendar-frozen 263 cross-market calibration research; never mutate live code."""
import argparse,collections,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/263'),str(ROOT/'research/263_independent_audit')]
from exp_263_batch import clean_rows
from chrono_goal_decision_263 import records_for_day
from chrono_goal_stage2_263 import load_predictions
from m4_integrated import use_lock
from audit import GROUP,SEVEN,add_nov8,checks,decisions,fit_direct,frozen_shrink,score_all,block_interval
from audit_full_history import EXPECTED_SHA,DEV_WINDOWS
FAMILIES=("MS","KG","O25")
RAW="FIXED_RAW_M4_MS_C3_OTHERS"
TRAIN25="FIXED_SHRINK_TRAIN_2025"
TRAIN25ND="FIXED_SHRINK_TRAIN_2025_NONDEV"
TRAIN26="FIXED_SHRINK_TRAIN_2026_AUGSEP"
LOGIT="LOGIT_TRAIN_2025_NONDEV"
BASE="ASOF_LEAGUE_RATE"
POLICIES=(RAW,TRAIN25,TRAIN25ND,TRAIN26,LOGIT,BASE,"C3","M4")

def isdev(date):
    return any(a<=date<b for a,b in DEV_WINDOWS)

def reconstruct_season(path):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==EXPECTED_SHA
    rows=clean_rows(path)
    assert len(rows)==4413
    season=[r for r in rows if r["season"]=="2025-2026"]
    assert len(season)==3533
    byleague=collections.defaultdict(list)
    for r in season:byleague[r["league"]].append(r)
    setting=use_lock(json.loads((ROOT/'experiments/263/m4_lock.json').read_text()))
    result=[];excluded=0
    for league in sorted(byleague):
        rr=sorted(byleague[league],key=lambda r:(r["match_date"],r["fixture_id"]))
        past=[];i=0
        while i<len(rr):
            day=rr[i]["match_date"];j=i
            while j<len(rr) and rr[j]["match_date"]==day:j+=1
            if len(past)>=60:
                got=records_for_day(past,rr[i:j],league,day,setting)
                assert len(got)==j-i
                for x in got:
                    assert x["base"] is not None
                    x["obs"]=x.pop("y")
                result.extend(got)
            else:excluded+=j-i
            past.extend(rr[i:j]);i=j
    assert (excluded,len(result))==(611,2922)
    assert len({r["id"] for r in result})==len(result)
    return result

def baseline_and_ensemble(rows):
    for r in rows:
        assert checks(r["base"])
        r["p"][BASE]=dict(r["base"])
        if "C3" in r["p"] and "M4" in r["p"]:
            q={k:(r["p"]["C3"][k]+r["p"]["M4"][k])*.5 for k in r["p"]["C3"]}
            assert checks(q)
            r["p"]["ENSEMBLE_50_50"]=q

def combine(r,ws=None):
    if "M4" not in r["p"] or "C3" not in r["p"]:return None
    p={}
    for fam,model in (("MS","M4"),("KG","C3"),("O25","C3")):
        weight=1 if ws is None else ws[model][fam]
        p.update({k:weight*r["p"][model][k]+(1-weight)*r["base"][k] for k in GROUP[fam]})
    assert checks(p)
    return p

def chosen_baseline(rows,policy):
    vals=[]
    for r in rows:
        if policy not in r["p"]:continue
        p=r["p"][policy];k=max(SEVEN,key=lambda x:p[x]);y=r["obs"][k]
        vals.append(((p[k]-y)**2,(r["base"][k]-y)**2))
    n=len(vals)
    return {"n":n,"selected_brier":round(sum(x for x,b in vals)/n,6) if n else None,
            "same_event_baseline_brier":round(sum(b for x,b in vals)/n,6) if n else None}

def reliability(rows,policy):
    bins=((0,.5),(.5,.6),(.6,.65),(.65,.70),(.70,.75),(.75,.8),(.8,1.0000001))
    data={f"{l:.2f}-{h:.2f}":[] for l,h in bins}
    for r in rows:
        if policy not in r["p"]:continue
        p=r["p"][policy];k=max(SEVEN,key=lambda x:p[x]);v=p[k]
        key=next(f"{l:.2f}-{h:.2f}" for l,h in bins if l<=v<h)
        data[key].append((v,r["obs"][k]))
    return {k:{"n":len(a),"avg_pred_pct":round(100*sum(v for v,y in a)/len(a),2) if a else None,
               "observed_pct":round(100*sum(y for v,y in a)/len(a),2) if a else None}
            for k,a in data.items()}

def describe(rows):
    out={}
    for name in POLICIES:
        out[name]={
            "proper_scores":{fam:score_all(rows,name,fam) for fam in FAMILIES},
            "one_best_event":decisions(rows,name),
            "same_event_baseline":chosen_baseline(rows,name),
            "reliability":reliability(rows,name),
            "minimum_60_65_70":{str(th):decisions(rows,name,th) for th in (.6,.65,.7)}
        }
    return out

def paired(rows):
    return {name:{fam:block_interval(rows,name,RAW,fam,nboot=750) for fam in FAMILIES}
            for name in (TRAIN25,TRAIN25ND,TRAIN26,LOGIT,BASE,"C3","M4")}

def league_splits(rows):
    result={}
    for lg in sorted({r["league"] for r in rows}):
        rr=[r for r in rows if r["league"]==lg]
        result[lg]={"n":len(rr),"scores":{name:{
            fam:score_all(rr,name,fam) for fam in FAMILIES}
            for name in (RAW,TRAIN25,TRAIN25ND,BASE)},
            "decision":{name:decisions(rr,name) for name in (RAW,TRAIN25ND,BASE)}}
    return result

def document(report):
    w=report["training_weights"]
    lines=["# 2.6.3 araştırması: KG ve 2.5 kalibrasyonu, 7 olaydan tek seçim","",
           "## Veri ve yöntem","",
           "Orijinal SHA sabit 4.413 maç; 2025/26 3.533 içinden ilk 611 başlangıç geçmişi, diğer 2.922 sadece önceki günle üretilen tahmin.",
           "Sonraki 2026/27 587 Ağustos-Eylül ve 293 Ekim kronolojik tahmin; 39 Kasım 8 orijinal SHA (tek gün).",
           "2025/26 sezonu M4 ayarlarının geliştirilmesinde kullanıldığı, 2026/27 daha önce araştırıldığı için hiçbir örneklem yeni kör final değildir.",
           "M4 için MS, C3 için KG/2.5. Ağırlık p = w x model + (1-w) x gün öncesi lig frekansı. w eğitim döneminde seçilip sonra donduruldu.",
           "","## Eğitimden dondurulan ağırlıklar","",
           "| Eğitim | M4 MS w | C3 KG w | C3 2.5 w |",
           "|---|---:|---:|---:|"]
    for name,ws in w.items():
        lines.append(f"| {name} | {ws['M4']['MS']} | {ws['C3']['KG']} | {ws['C3']['O25']} |")
    for period in ("2026_aug_sep_587","2026_oct_293","2026_nov8_sha_39","2026_all_880"):
        x=report["periods"][period]
        lines+=["",f"## {period}","",
                "| Seçici | MS n | MS Brier | KG Brier | O2.5 Brier | Tek seçim n | İsabet % | Ortalama tahmin % |",
                "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name in POLICIES:
            a=x[name];m=a["proper_scores"];d=a["one_best_event"]
            lines.append(f"| {name} | {m['MS']['n']} | {m['MS'].get('brier')} | {m['KG'].get('brier')} | {m['O25'].get('brier')} | {d['n']} | {d['hit_pct']} | {d['predicted_mean_pct']} |")
    lines+=["","## Doğruluk ve sınırlar","",
            "MS Brier, üç sınıfın Brier toplamı; KG ve 2.5 Brier tek ikili olaydır. Düşük iyi.",
            "Her maçtan en fazla bir olay seçildi. Aynı olayın lig geçmiş referans Brier'i de ölçüldü.",
            "Ayrıca 60/65/70 güven eşikleri, tahmin gerçekleşme güven tabloları, lig kesitleri, maç-günü bloklu belirsizlikler ham JSON'da bulunur.",
            "2026 Ağustos-Eylül eğitimli ağırlık o dönemde kullanılmadı: yalnız Ekim ve Kasım'a uygulandı.",
            "Ağırlıklar görülmüş sonuçlardan seçildiği için yeni maç önü kör kanıt olmadan canlı sisteme yükseltme yapılmaz.",
            "Canlı 2.6.3, sonuç/mühür arşivi, iş akışı, PDF, bahis otomasyonu değiştirilmedi; EV veya ROI hesaplanmadı.","",
            "Ayrıntılı veri: 07_calibration_result.json. Tekrar üretilebilir kaynak: audit_market_calibration.py."]
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    dev25=reconstruct_season(args.history)
    eval26=load_predictions(args.predictions)
    nov=add_nov8()
    assert len(eval26)==880 and len(nov)==39
    baseline_and_ensemble(dev25+eval26+nov)
    dev25_non=[r for r in dev25 if not isdev(r["date"])]
    aug=[r for r in eval26 if r["date"]<"2026-10-01"]
    octo=[r for r in eval26 if r["date"]>="2026-10-01"]
    assert (len(dev25_non),len(aug),len(octo))==(2220,587,293)
    weights={"train_2025_all":frozen_shrink(dev25),
             "train_2025_nondev":frozen_shrink(dev25_non),
             "train_2026_aug_sep":frozen_shrink(aug)}
    logistic_train=fit_direct(dev25_non,eval26+nov)
    for r in eval26+nov:
        variants={RAW:combine(r),
                  TRAIN25:combine(r,weights["train_2025_all"]),
                  TRAIN25ND:combine(r,weights["train_2025_nondev"])}
        if r["date"]>="2026-10-01":
            variants[TRAIN26]=combine(r,weights["train_2026_aug_sep"])
        if "DIRECT_LOGIT_C0.5" in r["p"]:
            variants[LOGIT]=r["p"]["DIRECT_LOGIT_C0.5"]
        for name,p in variants.items():
            if p is not None:r["p"][name]=p
    cohorts={"2026_aug_sep_587":aug,"2026_oct_293":octo,
             "2026_nov8_sha_39":nov,"2026_all_880":eval26}
    details={name:describe(rows) for name,rows in cohorts.items()}
    report={
        "schema":"263_MARKETWISE_DATE_FROZEN_CALIBRATION_RESEARCH_V1",
        "source_sha256":EXPECTED_SHA,
        "counts":{"source":4413,"original_2025_season":3533,"asof_2025":len(dev25),
                  "excluded_initial":611,"training_2025_nondev":len(dev25_non),
                  "asof_2026":len(eval26),"nov8_seals":len(nov)},
        "training_weights":weights,"logistic_train":logistic_train,
        "periods":details,
        "paired_day_cluster_bootstrap":{name:paired(rows) for name,rows in cohorts.items() if name!="2026_nov8_sha_39"},
        "by_league_october":league_splits(octo),
        "by_league_aug_sep":league_splits(aug),
        "history_not_blind":True,"past_M4_tuned_with_2025":True,
        "live_modified":False,"old_seals_modified":False,"model_promoted":False,
        "odds_profit_study":False,
        "nov8_one_day_and_not_all_official_score_ids_confirmed":True
    }
    dest=Path(args.outdir);dest.mkdir(parents=True,exist_ok=True)
    (dest/"07_calibration_result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (dest/"08_calibration_report.md").write_text(document(report),encoding="utf-8")
    summary={
       "weights":weights,"train_logit":logistic_train,
       "samples":report["counts"],
       "evaluation":{part:{k:{
           "MS":round(v["proper_scores"]["MS"].get("brier",-1),6),
           "KG":round(v["proper_scores"]["KG"].get("brier",-1),6),
           "O25":round(v["proper_scores"]["O25"].get("brier",-1),6),
           "n":v["one_best_event"]["n"],"hit":v["one_best_event"]["hit_pct"],
           "pred":v["one_best_event"]["predicted_mean_pct"]}
           for k,v in vals.items() if k in (RAW,TRAIN25,TRAIN25ND,TRAIN26,LOGIT,BASE)}
           for part,vals in details.items()}}
    print("CALIBRATION_RESEARCH_SUMMARY="+json.dumps(summary,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
