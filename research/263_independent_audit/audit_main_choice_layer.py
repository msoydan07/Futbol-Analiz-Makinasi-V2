"""Decision-layer diagnostic that mirrors active MS August joint calibration.

Historical as-of reconstruction is NOT same as live SHA decision and used no
November-8 observed outcome until post-date validation (the 39 are standalone).
2026 August fitted theta requires excluding August from valid evaluation.
"""
import argparse,collections,hashlib,json,math,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"experiments/263"),str(ROOT/"research/263_independent_audit")]
from exp_263_batch import clean_rows
from chrono_goal_decision_263 import score_markets
from chrono_goal_stage2_263 import load_predictions
from m4_integrated import fit_m4,predict_m4,use_lock
from model_first_decision_263 import joint_poisson
from audit import GROUP,SEVEN,checks,decisions,score_all,add_nov8
from audit_full_history import EXPECTED_SHA

PROXY="RAW_M4_MS_C3_BINARY"
LIVE_SHAPED="M4_AUG_JOINT_MS_C3_RAW_BINARY"
SHRUNK="M4_AUG_JOINT_MS_C3_025_BINARY"
LEAGUE="M4_AUG_JOINT_MS_LEAGUE_BINARY"
HISTORY39="M4_AUG_JOINT_MS_39_SHA_REF_NOT_TESTED"
SEED=26320261120
NAMES=(PROXY,LIVE_SHAPED,SHRUNK,LEAGUE)
FAMILY=lambda ev:"MS" if ev.startswith("MS") else "KG" if ev.startswith("BTTS") else "O25"

def reconstruct_m4_lambda(path,needed):
    raw=Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==EXPECTED_SHA
    allrows=clean_rows(path)
    assert len(allrows)==4413
    setting=use_lock(json.loads((ROOT/"experiments/263/m4_lock.json").read_text()))
    grouped=collections.defaultdict(list)
    for r in allrows:grouped[r["league"]].append(r)
    found={}
    for league in sorted(grouped):
        rr=sorted(grouped[league],key=lambda r:(r["match_date"],r["fixture_id"]))
        past=[];i=0
        while i<len(rr):
            day=rr[i]["match_date"];j=i
            while j<len(rr) and rr[j]["match_date"]==day:j+=1
            now=rr[i:j]
            selected=[r for r in now if r["fixture_id"] in needed]
            if selected:
                f4=fit_m4(past,league,day,setting)
                for r in selected:
                    found[r["fixture_id"]]=predict_m4(f4,r["home_id"],r["away_id"])
            past.extend(now);i=j
    assert set(found)==set(needed),"FORECAST_RECONSTRUCTION_WRONG_MATCH_IDS"
    return found

def build(r,theta,lam):
    if "M4" not in r["p"] or "C3" not in r["p"] or lam is None:return False
    lg0,lg1=lam
    rawp=score_markets(lg0,lg1)
    original=r["p"]["M4"]
    assert abs(rawp["1X2"]["H"]-original["MS1"])<.0000015
    assert abs(rawp["BTTS_YES"]-original["BTTS_YES"])<.0000015
    assert abs(rawp["OVER_2.5"]-original["OVER_2.5"])<.0000015
    newlh=max(.05,min(5.,math.exp(theta[0]+theta[2]*math.log(lg0))))
    newla=max(.05,min(5.,math.exp(theta[1]+theta[2]*math.log(lg1))))
    live_ms=joint_poisson(newlh,newla)
    raw={**{k:original[k] for k in GROUP["MS"]},
         **{k:r["p"]["C3"][k] for k in GROUP["KG"]+GROUP["O25"]}}
    variants={PROXY:raw}
    for name,w in ((LIVE_SHAPED,1.0),(SHRUNK,.25),(LEAGUE,0.)):
        probs={k:live_ms[k] for k in GROUP["MS"]}
        for fam in ("KG","O25"):
            probs.update({k:w*r["p"]["C3"][k]+(1-w)*r["base"][k] for k in GROUP[fam]})
        assert checks(probs)
        variants[name]=probs
    for n,p in variants.items():r["p"][n]=p
    return True

def winner(r,name):
    if name not in r["p"]:return None
    p=r["p"][name]
    choices=sorted(SEVEN,key=lambda k:(-p[k],k))
    best,second=choices[:2]
    return {"event":best,"prob":p[best],"y":r["obs"][best],
            "gap":p[best]-p[second],"runner":second,
            "runner_family":FAMILY(second),"family":FAMILY(best),
            "brier":(p[best]-r["obs"][best])**2}

def matched_compare(rows,name,baseline=LIVE_SHAPED):
    byday=collections.defaultdict(list);flip=collections.Counter()
    for r in rows:
        a=winner(r,name);b=winner(r,baseline)
        if not a or not b:continue
        flip["same_event" if a["event"]==b["event"] else "different_event"]+=1
        flip["same_family" if a["family"]==b["family"] else "different_family"]+=1
        byday[r["date"]].append((int(a["y"])-int(b["y"]),b["brier"]-a["brier"]))
    days=sorted(byday);pairs=[e for dt in days for e in byday[dt]]
    if not pairs:return {"n":0}
    mean=[sum(p[i] for p in pairs)/len(pairs) for i in range(2)]
    out={"n":len(pairs),"days":len(days),"hit_delta_pp":round(mean[0]*100,4),
         "selected_brier_improvement":round(mean[1],7),"choice_flip":dict(flip)}
    if len(days)>=4:
        rng=random.Random(SEED)
        bs=[[],[]]
        for _ in range(1300):
            block=[e for j in range(len(days)) for e in byday[rng.choice(days)]]
            for i in range(2):bs[i].append(sum(p[i] for p in block)/len(block))
        for z in bs:z.sort()
        out["hit_delta_95_pp"]=[round(bs[0][32]*100,4),round(bs[0][1267]*100,4)]
        out["brier_improvement_95"]=[round(bs[1][32],7),round(bs[1][1267],7)]
    return out

def ambiguity(rows,name):
    by=collections.defaultdict(list);gapcuts=(.01,.02,.03,.05,.1)
    for r in rows:
        w=winner(r,name)
        if not w:continue
        by["ALL"].append(w)
        by[w["family"]].append(w)
    result={}
    for fam,values in by.items():
        n=len(values)
        result[fam]={
            "n":n,"pct_gap_le_2pp":round(100*sum(x["gap"]<=.02 for x in values)/n,2),
            "pct_gap_le_5pp":round(100*sum(x["gap"]<=.05 for x in values)/n,2),
            "choice_accuracy_pct":round(100*sum(x["y"] for x in values)/n,2),
            "mean_reported_pct":round(100*sum(x["prob"] for x in values)/n,2),
            "gap_groups":{
                key:{
                    "n":len(a),"mean_pred_pct":round(100*sum(x["prob"] for x in a)/len(a),2) if a else None,
                    "hit_pct":round(100*sum(x["y"] for x in a)/len(a),2) if a else None}
                for key,a in {
                    "<=0.02":[x for x in values if x["gap"]<=.02],
                    "0.02-0.05":[x for x in values if .02<x["gap"]<=.05],
                    ">0.05":[x for x in values if x["gap"]>.05]}.items()}
        }
    return result

def summarize(rows):
    return {name:{"matches":len(rows),"eligible":sum(name in r["p"] for r in rows),
                  "family_scores":{f:score_all(rows,name,f) for f in GROUP},
                  "single_choice":decisions(rows,name),
                  "choice_margin":ambiguity(rows,name),
                  "paired_vs_live_shaped":matched_compare(rows,name)}
            for name in NAMES}

def report(d):
    lines=["# 2.6.3 ana tercih karar katmanı — aktif MS kalibrasyonunu koruyan kontrol","",
           "**Sınırlar:** Sadece araştırma dalı, mevcut 10 lig; xG ve piyasa oranı kullanılmadı. Bütün eski SHA, aktif kod, lock ve PDF dokunulmadı.",
           "Ağustos 2026'da öğrenilen M4 ortak MS kalibrasyonu geçerli tarih kullanımı açısından Ağustos'ta değerlendirilmedi. Eylül-Ekim orijinal SHA doğrulanmış tarih öncesi rekonstrüksiyon; yeni canlı mühür değildir.",
           "Bu geçmiş dönemlerde sonuçlar daha önce görüldüğü için yeni bağımsız kör test denemez. 8 Kasım 39 orijinal SHA ayrıca test edildi; tek gün sonuçları kesin kanıt değildir.",
           "Üretim kodu geçmiş 39 maçın benzer market olasılıklarından sınırlı güvenilirlik skoru hesaplar. Bu 39 sonuç Eylül-Ekim için **gelecek veridir**, dolayısıyla bu geçmiş günlere uygulanıp başarı uydurulmadı. Test edilen LIVE_SHAPED aktif kararın **M4 August MS + C3 RAW KG/O25 ham-yüzde sıralama parçasıdır**; 39 SHA tarihsel sıralama bileşenini kapsamaz.",
           "","## Maç başına tek olay — özet","",
           "| Dönem | Kural | n | İsabet % | Tahmini ort % | Seçim Brier | 2pp içinde iki tercih % |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for period in ("september","october","sept_october","nov8_sha"):
        for name in NAMES:
            x=d["periods"][period][name]
            dec=x["single_choice"];am=x["choice_margin"].get("ALL",{})
            lines.append(f"| {period} | {name} | {dec['n']} | {dec['hit_pct']} | {dec['predicted_mean_pct']} | {dec['selected_event_brier']} | {am.get('pct_gap_le_2pp')} |")
    lines+=["","## Aynı maç eşleştirme, belirsizlik","",
            "Bütün kararlarda aynı geçmiş maçlardan tek olay alınır; farklı olay seçildiğinde doğru/yaklış ve Brier farkı ayrı değerlendirilir. Bootstrap gün bazlıdır. Çoklu araştırma yapıldığı için tam bağımsız nihai üstünlük iddiası yoktur.",
            ""]
    for period in ("sept_october","october","nov8_sha"):
        lines+=["### "+period,""]
        for name in NAMES[1:]:
            x=d["periods"][period][name]["paired_vs_live_shaped"]
            lines.append(f"- {name}: {x}")
    lines+=["","## Karar mantığı","",
           "1. MS1/MSX/MS2 tek bir kalibre edilmiş M4 olasılık dağılımından gelir; KG ve 2.5 ayrı aile olasılıklarıdır. En yüksek % doğrudan kıyaslandığında aileler farklı kalibrasyona sahipse sıralama yanlı olabilir.",
           "2. Ana tercih öncesi her olayın aynı tarihe göre kalibre edilmiş gerçekleşme ihtimali gerekir. En çok hesaplanan değil, en çok **gerçekleşmesi beklenen** olay seçilmelidir.",
           "3. İlk iki adayın puan farkı çok dar olduğunda sonuçlar beraberlik içinde sayılmalı; bu güveni artırmaz. Mevcut ana tercih sessizce değiştirilmez.",
           "4. 39 tek-gün önceden mühürlü maç 7 bağımsız piyasa kanıtı değildir; gerçek mühür ve maç günü bağımsız doğrulama yayıldıkça aynı döneme ait eski maçları geriye dönük olarak kullanmak yasaktır.",
           "5. Bu karar katmanı araştırması bahis kârlılığı değil, olasılık sıralaması araştırmasıdır.",
           "","JSON: 12_main_choice_layer_result.json. Kaynak: audit_main_choice_layer.py."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",required=True)
    p.add_argument("--predictions",required=True)
    p.add_argument("--outdir",required=True)
    a=p.parse_args()
    lock=json.loads((ROOT/"experiments/263/model_first_selection_lock_20261120_normal_v3.json").read_text())
    theta=lock["m4_joint_calibration_august"]
    assert len(theta)==3 and lock["family_anchors"]=={"MS":"M4","KG":"C3","O25":"C3"}
    rows=load_predictions(a.predictions)
    assert len(rows)==880
    needed={r["id"] for r in rows if r["date"]>="2026-09-01"}
    lambdas=reconstruct_m4_lambda(a.history,needed)
    for r in rows:
        if r["id"] in needed:
            build(r,theta,lambdas[r["id"]])
    # November sealed M4 lambda from actual pre-kickoff archive; cannot reconstruct after KO.
    sealed=add_nov8()
    # The baseline audit read original signed payload for family markets.
    archive=json.loads((ROOT/"data/results_only_263/nov8_new100_terminal_archive_20261112.json").read_text())
    bykey={}
    for entry in archive["rows"]:
        if entry.get("score") is None:continue
        f=json.loads((ROOT/entry["forecast_path"]).read_text())
        fx=f["fixture"]
        bykey[fx["league"],fx["match_local_date"],f["payload_sha256"]]=f
    assert len(bykey)==39
    # add_nov8 original row lacked fixture SHA, so use archive ordering directly:
    # row order is archived original insertion ordering, checked with C3/M4 probabilities.
    novlambda=[]
    for entry in archive["rows"]:
        if entry.get("score") is None:continue
        f=json.loads((ROOT/entry["forecast_path"]).read_text())
        g=f["model_predictions"]["M4"]["goals"]
        novlambda.append((g["lambda_home"],g["lambda_away"],f))
    assert len(novlambda)==len(sealed)
    for r,(lh,la,original) in zip(sealed,novlambda):
        assert r["league"]==original["fixture"]["league"]
        assert abs(score_markets(lh,la)["1X2"]["H"]-r["p"]["M4"]["MS1"])<.0000015
        build(r,theta,(lh,la))
    september=[r for r in rows if r["date"][:7]=="2026-09"]
    october=[r for r in rows if r["date"][:7]=="2026-10"]
    valid=september+october
    assert (len(september),len(october),len(valid),len(sealed))==(328,293,621,39)
    result={"schema":"263_MAIN_CHOICE_WITH_M4_JOINT_MS_RECONSTRUCTION_V1",
            "source_sha256":EXPECTED_SHA,"live_ms_lock_sha":lock["payload_sha256"],
            "valid_historical_cohorts":{"sept":328,"oct":293,"sept_oct":621,"nov8":39},
            "ms_calibration_theta_frozen_in_august":theta,
            "no_39_sha_historical_reference_applied_to_past":True,
            "nov8_single_day_does_not_calibrate_itself":True,
            "research_only":True,"live_decision_unchanged":True,
            "seals_unchanged":True,"no_odds_xg_or_profit_claim":True,
            "not_a_full_exact_replay_of_39_sha_historical_ranker":True,
            "periods":{k:summarize(v) for k,v in (
                ("september",september),("october",october),
                ("sept_october",valid),("nov8_sha",sealed))}}
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    (out/"12_main_choice_layer_result.json").write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    (out/"13_main_choice_layer_report.md").write_text(report(result))
    print("MAIN_CHOICE_RESULT="+json.dumps({
        period:{n:{"n":v["single_choice"]["n"],
                   "hit":v["single_choice"]["hit_pct"],
                   "conf":v["single_choice"]["predicted_mean_pct"],
                   "margin2":v["choice_margin"].get("ALL",{}).get("pct_gap_le_2pp"),
                   "paired":v["paired_vs_live_shaped"]} for n,v in rr.items()}
        for period,rr in result["periods"].items()},sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
