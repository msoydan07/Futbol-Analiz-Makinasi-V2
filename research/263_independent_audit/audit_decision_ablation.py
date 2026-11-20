"""Shadow-only diagnostic: preserve MS M4 and isolate KG/2.5 shrinkage.
Four explicit ablations: raw, frozen previous-season 25/25, 2026-dev 50/25,
and past-league-only 0/0. Never change original models or forecast seals.
"""
import argparse,collections,json,math,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/263'),str(ROOT/'research/263_independent_audit')]
from audit import GROUP, SEVEN, add_nov8, checks, decisions, score_all
from chrono_goal_stage2_263 import load_predictions
from audit_full_history import EXPECTED_SHA
from audit_market_calibration import RAW,BASE,baseline_and_ensemble

P25="MS_M4_RAW_KG_C3_025_O25_C3_025"
P50="MS_M4_RAW_KG_C3_050_O25_C3_025"
P00="MS_M4_RAW_KG_LEAGUE_O25_LEAGUE"
NAMES=(RAW,P25,P50,P00)
SEED=26320261120

def forecast(r,kg_weight,o25_weight):
    if "M4" not in r["p"] or "C3" not in r["p"]:return None
    p={}
    for f,model,w in (("MS","M4",1),("KG","C3",kg_weight),("O25","C3",o25_weight)):
        p.update({k:w*r["p"][model][k]+(1-w)*r["base"][k] for k in GROUP[f]})
    assert checks(p)
    return p

def selected(r,name):
    if name not in r['p']:return None
    p=r['p'][name];ev=max(SEVEN,key=lambda k:p[k])
    return {'ev':ev,'prob':p[ev],'y':r['obs'][ev],
            'loss':(p[ev]-r['obs'][ev])**2,
            'base_loss':(r['base'][ev]-r['obs'][ev])**2}

def paired_choice(rows,name,benchmark=RAW):
    bydate=collections.defaultdict(list)
    changes=collections.Counter()
    for r in rows:
        a,b=selected(r,name),selected(r,benchmark)
        if not a or not b:continue
        bydate[r["date"]].append((a['y']-b['y'],b['loss']-a['loss'],
                                  a['base_loss']-a['loss']))
        changes["same_event" if a['ev']==b['ev'] else "different_event"]+=1
        aa,bb=a["ev"],b["ev"]
        family=lambda x:"MS" if x.startswith("MS") else "KG" if x.startswith("BTTS") else "O25"
        changes["same_family" if family(aa)==family(bb) else "different_family"]+=1
    allvals=[v for daily in bydate.values() for v in daily]
    if not allvals:return {"n":0}
    n=len(allvals)
    means=[sum(x[i] for x in allvals)/n for i in range(3)]
    days=sorted(bydate)
    if len(days)<4:
        ci=[None,None,None]
    else:
        rng=random.Random(SEED);sims=[[],[],[]]
        for b in range(1400):
            sampled=[v for _ in days for v in bydate[rng.choice(days)]]
            for i in range(3):
                sims[i].append(sum(x[i] for x in sampled)/len(sampled))
        ci=[]
        for v in sims:
            v.sort();ci.append([round(v[35],7),round(v[1365],7)])
    return {"n":n,"days":len(days),"hit_advantage_candidate_percentage_points":round(100*means[0],3),
            "hit_advantage_ci95_pp":[round(100*ci[0][0],3),round(100*ci[0][1],3)] if ci[0] else None,
            "selected_brier_gain_candidate":round(means[1],7),
            "selected_brier_gain_ci95":ci[1],
            "same_event_brier_gain_vs_league":round(means[2],7),
            "same_event_vs_league_ci95":ci[2],
            "choice_changes":dict(changes)}

def describe(rows):
    return {name:{
        "market_scores":{fam:score_all(rows,name,fam) for fam in GROUP},
        "single_event":decisions(rows,name),
        "p65":decisions(rows,name,.65),
        "paired_vs_raw":paired_choice(rows,name)}
        for name in NAMES}

def write_md(d):
    table=[
        "# 2.6.3 — Son ayrıştırma: MS modelini koru, KG ve 2.5'i ayrı düzelt",
        "",
        "Bu çalışma ilk 2025/26 ve 2026/27 kalibrasyon çalışmalarının takip tanı testidir.",
        "Hiperparametreler ve alternatifler daha önce araştırılmış verilere göre seçilmiş olduğu için sonuçlar yeni kör kanıt değildir.",
        "Kaynak: aynı SHA doğrulanan orijinal 4.413 maç, 2026/27 880 tarih bazlı tahmin, ayrıca 8 Kasım 39 maç önü SHA.",
        "Yalnız M4 MS hamı ve C3 KG/2.5 + o günden önceki lig frekansı karışımı; aile bazlı tek olay seçimi.",
        "",
        "## Aday ağırlıkları (MS M4 her zaman 1.0)",
        "",
        "- RAW: KG C3=1, 2.5 C3=1; önceki aktif benzeri ham aile yönlendirmesi.",
        "- P25: KG C3=0.25, 2.5 C3=0.25 (2025/26 geliştirme-dışı öğrenilmiş, 2026/27'ye dondurulmuş).",
        "- P50: KG C3=0.50, 2.5 C3=0.25 (2026 Ağustos-Eylül öğrenilmiş; SADECE Ekim ve Kasım'da incelendi).",
        "- P00: KG ve 2.5 C3=0, yalnız önceki günün lig frekansı.",
        "",
    ]
    for label in ("aug_sep","october","nov8_sha","original_880"):
        rows=d["periods"][label]
        table += [f"## {label}","",
                  "| Aday | n | MS Brier | KG Brier | 2.5 Brier | Tek seçim % | Tahmin % | n(>=65) | >=65 isabet % |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name in NAMES:
            v=rows[name];s=v["market_scores"];c=v["single_event"];t=v["p65"]
            table.append(f"| {name} | {c['n']} | {s['MS'].get('brier')} | {s['KG'].get('brier')} | {s['O25'].get('brier')} | {c['hit_pct']} | {c['predicted_mean_pct']} | {t['n']} | {t['hit_pct']} |")
        table+=["","Eşleştirilmiş hit farkı ve Brier farkı %95 tarih-gün blok bootstrap dahil JSON dosyasındadır.", ""]
    table += ["## Nihai araştırma güvenlik kapısı","",
        "2025/26 M4 parametre geliştirme dönemi ve 2026/27 daha önce araştırılmıştır: bağımsız kör sonuç yok.",
        "8 Kasım 39 mühür tek maç günü olduğu için aralık hesaplanmaz ve tek başına üretim terfisi için kullanılamaz.",
        "Farklı yedi olay birbirinden bağımsız değildir, maç başına en fazla bir seçim yapılmıştır.",
        "Sonuçlar canlı 2.6.3 motoru, mühürleri, mevcut günlük/haftalık takip işleri veya bahis kuralları üzerinde hiçbir değişiklik yapmaz.",
        "Piyasadan maç önü oranı ve EV/ROI olmadığından bahis kârlılığı iddia edilmez.",
        "",
        "Ham çıktı: 09_decision_ablation_result.json; test kodu: audit_decision_ablation.py."]
    return "\n".join(table)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    old=json.loads((ROOT/"research/263_independent_audit/07_calibration_result.json").read_text())
    assert old["source_sha256"]==EXPECTED_SHA
    assert (old["training_weights"]["train_2025_nondev"]["C3"]["KG"],
            old["training_weights"]["train_2025_nondev"]["C3"]["O25"]) == (.25,.25)
    assert (old["training_weights"]["train_2026_aug_sep"]["C3"]["KG"],
            old["training_weights"]["train_2026_aug_sep"]["C3"]["O25"]) == (.5,.25)
    src=load_predictions(args.predictions)
    nov=add_nov8()
    assert len(src)==880 and len(nov)==39
    baseline_and_ensemble(src+nov)
    aug=[r for r in src if r["date"]<"2026-10-01"]
    october=[r for r in src if r["date"]>="2026-10-01"]
    assert (len(aug),len(october))==(587,293)
    for r in src+nov:
        for name,k,o in ((RAW,1,1),(P25,.25,.25),(P00,0,0)):
            q=forecast(r,k,o)
            if q:r["p"][name]=q
        if r["date"]>="2026-10-01":
            q=forecast(r,.5,.25)
            if q:r["p"][P50]=q
    cuts={"aug_sep":aug,"october":october,
          "nov8_sha":nov,"original_880":src}
    out={
        "schema":"263_ONE_EVENT_MS_RAW_KG_O25_SHRINK_ABLATION_V1",
        "original_sha256":EXPECTED_SHA,
        "weights_2025_frozen":{"MS_M4":1,"KG_C3":.25,"O25_C3":.25},
        "weights_2026_augsep_frozen":{"MS_M4":1,"KG_C3":.5,"O25_C3":.25},
        "periods":{k:describe(v) for k,v in cuts.items()},
        "research_only":True,"does_not_change_main":True,
        "old_forecast_seals_unchanged":True,
        "no_blind_claim":True,"market_prices_available":False,
        "nov_single_day_score_id_limit":True}
    dest=Path(args.outdir);dest.mkdir(parents=True,exist_ok=True)
    (dest/"09_decision_ablation_result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (dest/"10_decision_ablation_report.md").write_text(write_md(out),encoding="utf-8")
    print("DECISION_ABLATION_SUMMARY="+json.dumps({
        period:{name:{
            "n":v["single_event"]["n"],"hit":v["single_event"]["hit_pct"],
            "conf":v["single_event"]["predicted_mean_pct"],
            "selected_brier":v["single_event"]["selected_event_brier"],
            "p65":v["p65"]["n"],"p65hit":v["p65"]["hit_pct"],
            "paired":v["paired_vs_raw"]}
            for name,v in values.items()}
        for period,values in out["periods"].items()},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
