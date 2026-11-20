"""Large retrospective main-choice historical reliability audit, no live edits.

3802 date-wise as-of reconstructions != 3802 sealed pre-kickoff forecasts.
First compare raw M4 MS + raw C3 KG/2.5 over original 2025/26 and 2026/27.
Then exactly frozen August-calibrated M4 joint MS on Sep-Oct 2026 only.
A day's completed results never enter decisions for that same day (any league).
"""
import argparse,bisect,collections,csv,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"experiments/263"),str(ROOT/"research/263_independent_audit")]
from audit import GROUP,SEVEN,checks
from audit_market_calibration import reconstruct_season
from audit_main_choice_layer import reconstruct_m4_lambda,build,LIVE_SHAPED
from chrono_goal_stage2_263 import load_predictions
from audit_full_history import EXPECTED_SHA

RAW="RAW_MAX"
FORMULA="PAST_20PRIOR_NO_SUPPORT_GATE"
GUARD20="PAST_20PRIOR_ONLY_WHEN_N20"
GUARD50="PAST_20PRIOR_ONLY_WHEN_N50"
POOLED="TEN_LEAGUE_ONLY_20PRIOR"
NORMAL="PAST_20PRIOR_N20_NORMALIZED"
SHRINK="M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE"
RULES=(RAW,FORMULA,GUARD20,GUARD50,POOLED,NORMAL,SHRINK)
SEED=26320261120

def attach_ids(rows,csvpath):
    ids=[];seen=set()
    with Path(csvpath).open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            fid=r["fixture_id"]
            if fid not in seen:ids.append(fid);seen.add(fid)
    assert len(ids)==len(rows)
    for r,fid in zip(rows,ids):r["id"]=fid

def vector(r,mode):
    if mode=="FROZEN":return r["p"].get(LIVE_SHAPED)
    if "M4" not in r["p"] or "C3" not in r["p"]:return None
    p={**{k:r["p"]["M4"][k] for k in GROUP["MS"]},
       **{k:r["p"]["C3"][k] for k in GROUP["KG"]+GROUP["O25"]}}
    assert checks(p);return p

class Index:
    def __init__(self):
        self.pool={k:[] for k in SEVEN}
        self.local=collections.defaultdict(lambda:{k:[] for k in SEVEN})
    def add(self,r,p):
        for k in SEVEN:
            pt=(p[k],int(r["obs"][k]))
            bisect.insort(self.pool[k],pt)
            bisect.insort(self.local[r["league"]][k],pt)
    def window(self,arr,p):
        lo=bisect.bisect_left(arr,(p-.05,-1))
        hi=bisect.bisect_right(arr,(p+.05,2))
        a=arr[lo:hi]
        return len(a),sum(y for _,y in a)
    def evidence(self,r,k,p):
        local=self.window(self.local[r["league"]][k],p)
        pooled=self.window(self.pool[k],p)
        return (local if local[0]>=8 else pooled),pooled

def posterior(p,n,w):
    return (20*p+w)/(20+n)

def calc(r,p,index):
    values={name:dict(p) for name in RULES}
    support={}
    for k in SEVEN:
        (n,w),(all_n,all_w)=index.evidence(r,k,p[k])
        v=posterior(p[k],n,w)
        values[FORMULA][k]=v
        values[GUARD20][k]=v if n>=20 else p[k]
        values[GUARD50][k]=v if n>=50 else p[k]
        values[POOLED][k]=posterior(p[k],all_n,all_w)
        support[k]=n
    for fam,keys in GROUP.items():
        total=sum(values[GUARD20][k] for k in keys)
        for k in keys:values[NORMAL][k]=values[GUARD20][k]/total
        w=1.0 if fam=="MS" else .25
        for k in keys:values[SHRINK][k]=w*p[k]+(1-w)*r["base"][k]
    assert all(checks(values[n]) for n in (RAW,NORMAL,SHRINK))
    return values,support

def fam(k):
    return "MS" if k in GROUP["MS"] else "KG" if k in GROUP["KG"] else "O25"

def process(rows,mode):
    rr=sorted(rows,key=lambda r:(r["date"],r["league"],r["id"]))
    assert len(set(r["id"] for r in rr))==len(rr)
    idx=Index();out=[];i=0
    while i<len(rr):
        date=rr[i]["date"];j=i
        while j<len(rr) and rr[j]["date"]==date:j+=1
        batch=[]
        for r in rr[i:j]:
            p=vector(r,mode)
            if p is None:continue
            v,n=calc(r,p,idx)
            choices={}
            for name,probs in v.items():
                sortedkeys=sorted(SEVEN,key=lambda k:(-probs[k],k))
                main,second=sortedkeys[:2]
                choices[name]={"event":main,"family":fam(main),
                               "p":round(probs[main],9),
                               "y":int(r["obs"][main]),
                               "loss":(probs[main]-r["obs"][main])**2,
                               "gap":round(probs[main]-probs[second],9)}
            raw=choices[RAW]["event"]
            out.append({"id":r["id"],"date":date,"league":r["league"],
                        "prior_match_count_for_raw_choice":n[raw],
                        "choices":choices})
            batch.append((r,p))
        for r,p in batch:idx.add(r,p)
        i=j
    return out

def summarize_one(rows,name):
    items=[r["choices"][name] for r in rows];n=len(items)
    if not n:return {"n":0}
    return {"n":n,"hit_pct":round(100*sum(x["y"] for x in items)/n,3),
            "mean_pred_pct":round(100*sum(x["p"] for x in items)/n,3),
            "selected_brier":round(sum(x["loss"] for x in items)/n,7),
            "gap_le_2pp_pct":round(100*sum(x["gap"]<=.02 for x in items)/n,2),
            "market_counts":dict(sorted(collections.Counter(x["event"] for x in items).items()))}

def paired(rows,name):
    byday=collections.defaultdict(list);changed=0
    for r in rows:
        a=r["choices"][name];b=r["choices"][RAW]
        changed+=a["event"]!=b["event"]
        byday[r["date"]].append((a["y"]-b["y"],b["loss"]-a["loss"]))
    vals=[v for daily in byday.values() for v in daily]
    if not vals:return {"n":0}
    n=len(vals)
    result={"n":n,"days":len(byday),"changed_event":changed,
            "hit_gain_pp":round(100*sum(x for x,_ in vals)/n,4),
            "selected_brier_gain":round(sum(y for _,y in vals)/n,8)}
    if len(byday)>=4:
        dates=sorted(byday);rng=random.Random(SEED);hit=[];brier=[]
        for _ in range(1200):
            samp=[v for __ in dates for v in byday[rng.choice(dates)]]
            hit.append(100*sum(x for x,_ in samp)/len(samp))
            brier.append(sum(y for _,y in samp)/len(samp))
        hit.sort();brier.sort()
        result["hit_gain_95_pp"]=[round(hit[30],3),round(hit[1170],3)]
        result["brier_gain_95"]=[round(brier[30],8),round(brier[1170],8)]
    return result

def summary(rows):
    return {"n":len(rows),"days":len(set(r["date"] for r in rows)),
            "n_prior_ge_20":sum(r["prior_match_count_for_raw_choice"]>=20 for r in rows),
            "n_prior_ge_50":sum(r["prior_match_count_for_raw_choice"]>=50 for r in rows),
            "metrics":{k:summarize_one(rows,k) for k in RULES},
            "paired_vs_raw":{k:paired(rows,k) for k in RULES if k!=RAW}}

def markdown(d):
    lines=[
      "# 2.6.3 — Daha fazla maçla ana tercih güvenilirliği karşılaştırması",
      "",
      "Araştırma dalında tamamlanan geriye dönük tarih-sıralı deney: **3.802 değerlendirme maçı; 39 gerçek SHA değil**.",
      "",
      "2025/26 2.922 as-of maç ve 2026/27 880 as-of maç (M4 ham MS, C3 ham KG/2.5).",
      "Ek ayrı 2026 Eylül-Ekim 621 kaynak maçta dondurulmuş Ağustos ortak MS kalibrasyonuyla canlıya yakın varyant.",
      "As-of olayın kendisi, aynı maç gününün başka lig sonuçları ve gelecek skorlar eğitim arşivine dahil edilmez.",
      "39 SHA yalnız gerçek pre-kickoff mühür kanıtıdır; diğerleri doğrulanmış as-of geriye dönük yeniden hesaplamadır.",
      "",
      "## Karar katmanı seçenekleri",
      "",
      "- RAW_MAX: En büyük olasılık.",
      "- PAST_20PRIOR_NO_SUPPORT_GATE: mevcut sıralamaya benzer (20*p + geçmiş isabet)/(20+n); yerel ligde n>=8 varsa yerel, değilse tüm lig.",
      "- PAST_20PRIOR_ONLY_WHEN_N20: n<20 ise mevcut model yüzdesine dön.",
      "- PAST_20PRIOR_ONLY_WHEN_N50: n<50 ise mevcut model yüzdesine dön.",
      "- TEN_LEAGUE_ONLY_20PRIOR: yalnız tüm lig, yerel örnek yok.",
      "- PAST_20PRIOR_N20_NORMALIZED: n<20 fallback, sonra üç olay ailesi kendi içinde toplam 1 olacak biçimde normalize.",
      "- M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE: M4 MS aynen; KG ve 2.5 için C3'ün %25'i, maç gününden önceki lig bazının %75'i.",
      "",
      "## Dönem bazlı sonuçlar",
      ""]
    for period,pr in d["periods"].items():
        lines.extend([f"### {period} ({pr['n']} maç / {pr['days']} gün)","",
                    "| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |",
                    "|---|---:|---:|---:|---:|---:|"])
        for name,met in pr["metrics"].items():
            nchange=pr["paired_vs_raw"].get(name,{}).get("changed_event",0)
            lines.append(f"| {name} | {met['n']} | {met.get('hit_pct')} | {met.get('mean_pred_pct')} | {met.get('selected_brier')} | {nchange} |")
        lines.append("")
    lines.extend(["## Sınırlamalar","",
                  "- Aynı olay ve benzer olasılık bandı (±5 puan), önceki gün sonuçları. Tek maç yedi bağımsız bahis değildir.",
                  "- Eski dönemde kullanılan M4 sürümü ile Ağustos'ta kalibre edilen MS sürümü birbirine geçmiş kayıt diye karıştırılmadı.",
                  "- M4'ün 2025/26 ayar dönemini ve daha önce araştırılmış 2026/27 sonuçlarını yeniden değerlendirmek tamamen yeni kör test değildir.",
                  "- Üretimdeki tam karar kodu tarihsel 39 gerçek mühür için ayrı sınır uygular; buradaki 3.802 as-of denemesi onun gerçek mühür havuzuna eklenmedi.",
                  "- Oran, xG, kâr, ROI, aktif model, ana mühürler ve otomasyonlar değişmedi.",
                  "","JSON: 15_historical_ranker_large_sample.json; betik: audit_ranker_large_sample.py."])
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    assert hashlib.sha256(Path(a.history).read_bytes()).hexdigest()==EXPECTED_SHA
    s25=reconstruct_season(a.history)
    s26=load_predictions(a.predictions)
    attach_ids(s26,a.predictions)
    assert len(s25)==2922 and len(s26)==880
    both=process(s25+s26,"RAW")
    current=[r for r in s26 if r["date"]>="2026-09-01"]
    lock=json.loads((ROOT/"experiments/263/model_first_selection_lock_20261120_normal_v3.json").read_text())
    lam=reconstruct_m4_lambda(a.history,{r["id"] for r in current})
    for r in current:
        build(r,lock["m4_joint_calibration_august"],lam[r["id"]])
    live=process(current,"FROZEN")
    periods={
        "2025_26_datewise_2922":[r for r in both if r["date"]<"2026-07-01"],
        "2026_27_datewise_880":[r for r in both if r["date"]>="2026-07-01"],
        "all_asof_3802":both,
        "2026_sep_oct_frozen_MS":live,
        "2026_oct_only_frozen_MS":[r for r in live if r["date"]>="2026-10-01"],
    }
    d={"schema":"263_LARGE_ASOF_HISTORICAL_MAIN_RANKING_V1",
       "source_sha256":EXPECTED_SHA,
       "raw_asof_2025":len(s25),"raw_asof_2026":len(s26),
       "original_sha_seals":39,
       "retro_asof_not_real_sha":True,
       "original_live_code_unchanged":True,
       "same_date_leakage_prevented":True,
       "prior_strength":20,"window_probability_width":.05,
       "periods":{k:summary(v) for k,v in periods.items()}}
    target=Path(a.outdir);target.mkdir(parents=True,exist_ok=True)
    (target/"15_historical_ranker_large_sample.json").write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (target/"16_historical_ranker_large_sample_report.md").write_text(markdown(d),encoding="utf-8")
    print("LARGE_DECISION_AUDIT="+json.dumps({
       "n":{k:v["n"] for k,v in d["periods"].items()},
       "results":{period:{p:{"hit":vals["hit_pct"],"pred":vals["mean_pred_pct"],
           "brier":vals["selected_brier"],"flip":x["paired_vs_raw"].get(p,{}).get("changed_event",0),
           "hit_ci":x["paired_vs_raw"].get(p,{}).get("hit_gain_95_pp")}
           for p,vals in x["metrics"].items()} for period,x in d["periods"].items()}},
       ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
