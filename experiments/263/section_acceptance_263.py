"""Read-only 17-section completion gate for the 2.6.3 OFFLINE operational report.

It does not run retrospective experiments, scrape fixtures, choose bets, or
certify any live match. Every section is labeled with its actual evidence.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from quality_gate_263 import HISTORICAL_SHA256
from decision_preflight_263 import SIDE, GENERAL, WATCH_MARKETS, VERSION as PREFLIGHT_VERSION

VERSION = '263_section_contract_gate_v1'
HEADINGS = (
 'Ana görev ve öncelik', 'Güncel veri ve kaynak protokolü',
 'Maç önü veri bütünlüğü', 'Takım formu, rakip kalitesi ve veri kalitesi',
 'Kadro, taktik, psikoloji ve koşullar', 'İstatistiksel model ve olasılıklar',
 'Elo takım gücü kontrolü', 'Maç sonucu 1-X-2', 'Gol pazarları',
 'İlk yarı ve doğru skor', 'Korner pazarı', 'En olası tercihler',
 'Matematiksel değerli seçimler', 'Güven, risk ve belirsizlik',
 'Sonuç sunumu', 'Maç önü kayıt ve maç sonu değerlendirme',
 '25 maçlık pilot test'
)
BLOCKERS = (
 'CANLI_MAC_BAGLANTISI_VE_KAYNAK_GUNCELLIGI_GEREKLI',
 'KADRO_VE_KRITIK_HABERLER_GUNCEL_KAYNAKTAN_DOGRULANMADI',
 'C2_KAPSAM_VE_KALIBRASYON_YETERSIZ',
 'A_B_C_SECIMI_HENUZ_ONAYLANMADI',
 'ORAN_EV_VE_SABIT_TAHMIN_DEFTERI_SONRAKI_ASAMA',
 'BAGIMSIZ_ILERI_KABUL_HENUZ_YOK',
)
class SectionAcceptanceError(ValueError):
    pass

def _require(condition, reason):
    if not condition:
        raise SectionAcceptanceError(reason)

def _probabilities(markets, label):
    _require(isinstance(markets,dict),'missing '+label+' markets')
    for name,val in markets.items():
        _require(isinstance(val,(int,float)) and not isinstance(val,bool) and math.isfinite(val) and 0<=val<=1,
                 label+' invalid probability '+name)
    for name in ('MS1','MSX','MS2','1X','X2','12','BTTS_YES','BTTS_NO','OVER_2.5','UNDER_2.5'):
        _require(name in markets,label+' missing '+name)
    pairs=[('MS1','MSX','MS2'),('1X','MS1','MSX'),('X2','MSX','MS2'),('12','MS1','MS2')]
    for k,a,b in pairs:
        expected=1 if k=='MS1' else markets[a]+markets[b]
        actual=sum(markets[q] for q in ('MS1','MSX','MS2')) if k=='MS1' else markets[k]
        _require(abs(actual-expected)<1e-7,label+' incoherent 1X2/double-chance')
    for x,y in [('BTTS_YES','BTTS_NO'),('OVER_2.5','UNDER_2.5')]:
        _require(abs(markets[x]+markets[y]-1)<1e-7,label+' incoherent complements')

def audit(bundle):
    _require(isinstance(bundle,dict),'not a report object')
    _require(bundle.get('scope')=='HYPOTHETICAL_OFFLINE_AUDIT','fake offline scope')
    _require(bundle.get('not_live_match_analysis') is True and bundle.get('real_fixture_verified') is False,'live fixture wrongly asserted')
    _require(bundle.get('does_not_claim_live_readiness') is True,'live readiness wrongly asserted')
    _require(bundle.get('production_changed') is False and bundle.get('model_b_parameters_modified') is False
             and bundle.get('c2_parameters_modified') is False,'production/math parameters changed')
    _require(bundle.get('odds_EV') is None and bundle.get('recommendations')==[] and bundle.get('model_promotions')==[],
             'unapproved bets, EV or model promotion')
    src=bundle.get('data_provenance',{})
    _require(src.get('sha256')==HISTORICAL_SHA256 and src.get('rows')==4413,'frozen historical evidence mismatch')
    _require(bundle.get('acceptance_sha256')==HISTORICAL_SHA256,'acceptance source mismatch')
    policy=bundle.get('weekly_update_policy',{})
    _require(policy.get('day')=='TUESDAY' and policy.get('timezone')=='Europe/Istanbul'
             and policy.get('automation_verified') is False and policy.get('historical_base_immutable') is True,
             'Tuesday/no-automation policy mismatch')
    sections=bundle.get('sections',[])
    _require(isinstance(sections,list) and len(sections)==17,'incorrect section count')
    _require([x.get('number') for x in sections]==list(range(1,18)),'section numbering mismatch')
    _require(tuple(x.get('title') for x in sections)==HEADINGS,'section titles mismatch')
    cases=bundle.get('cases')
    _require(isinstance(cases,list) and 1<=len(cases)<=20,'invalid case count')
    case_results=[]
    for i,e in enumerate(cases,1):
        c=e['identity']; analysis=e['analysis']; q=e['quality']; dc=e['data_context']; b=e['model_b_existing']
        arb=e['model_arbitration']; ranking=e['probability_ranking']; xg=e['descriptive_xg']
        _require(c['target_date']==dc['cutoff_exclusive']==b['source_cutoff_exclusive']==
                 analysis['provenance']['cutoff_exclusive_date'], 'case cutoff mismatch')
        _require(analysis['fixture_verified'] is False and analysis['is_real_match_forecast'] is False and
                 q['fixture_verified'] is False and q['is_real_match_forecast'] is False, 'historical case certified live')
        _require(q['recommendations']==[] and q['best_pick'] is None and
                 q['high_probability_alert'] is None and q['odds_or_EV'] is None,'unauthorized quality recommendation')
        _require(all(m.get('can_recommend') is False and m.get('calibrated') is False for m in
                     q['markets']+q['experimental_audit']), 'unapproved market calibration')
        _require(arb['automatic_fallback_promoted'] is False and arb['c3_status']=='SEPARATE_EXPERIMENT_ONLY',
                 'automatic promotion of unvalidated model')
        _require(ranking['recommended'] is False,'ranking masquerades as recommendation')
        _require(xg['used_as_lambda_multiplier'] is False and xg['used_to_select_primary_model'] is False,
                 'xG silently changed math')
        _require(e['external_factors']['verified_external_lambda_adjustments']==0,'unverified external lambda correction')
        _require(e['data_context']['recommendation_eligible'] is False,'context recommended a bet')
        _require(e['data_context']['confidence_eligible'] is False,'context implied calibrated confidence')
        c2=analysis['model_outputs'].get('C2')
        if c2:
            _require(arb['canonical_primary']=='C2' and
                     arb['canonical_status']=='CALCULATED_NOT_FORWARD_VALIDATED','bad canonical C2 label')
            _require(c2['details']['k']==5 and c2['details']['w']==0.5,'C2 constants drifted')
            _require(abs(c2['goals']['probability_sum']-1)<1e-7,'C2 matrix not normalized')
            _probabilities(c2['goals']['markets'],'C2')
        else:
            _require(arb['canonical_primary'] is None and
                     arb['canonical_status']=='YOK_INSUFFICIENT_CONTEXT', 'fake C2 availability')
        if b.get('probabilities'):
            p=b['probabilities']
            _require(all(isinstance(p.get(k),(int,float)) and 0<=p[k]<=1 for k in ('MS1','MSX','MS2')),
                     'invalid existing Model B probabilities')
            _require(abs(sum(p[k] for k in ('MS1','MSX','MS2'))-1)<1e-7,'Model B 1X2 not normalized')
        allowed_model='C2_CANONICAL' if c2 else ('C1_EXPLORATORY_ONLY_C2_MISSING' if b.get('probabilities') else None)
        _require(ranking['model']==allowed_model,'ranking uses an unauthorized model')
        _require(all(isinstance(r.get('probability'),(float,int)) and 0<=r['probability']<=1
                     for r in ranking['rows']),'invalid displayed probability')
        _require(not any('FIRST_HALF_CORNERS' in str(k).upper() for k in analysis['other_markets']),
                 'removed first-half corner market reappeared')
        # Contract 12-14: descriptive math and WATCH are never A/B/C, GEÇTİ, EV or a real pick.
        dp=e.get('decision_preflight_263')
        _require(isinstance(dp,dict) and dp.get('version')==PREFLIGHT_VERSION, 'decision preflight missing')
        _require(dp.get('league')==c['league'] and dp.get('cutoff_exclusive')==c['target_date'],
                 'decision preflight wrong match/cutoff')
        _require(dp.get('canonical_model')==('C2' if c2 else None), 'preflight fake primary')
        _require(dp.get('recommendation_eligible') is False and dp.get('pilot_record_eligible') is False
                 and dp.get('independent_forward_validation') is False, 'preflight falsely approved')
        _require(dp.get('A_B_C_official_candidates')==[] and dp.get('passed_filter')==[]
                 and dp.get('value_selections')==[] and dp.get('odds_or_EV') is None,
                 'preflight fabricated picks or value')
        candidates=dp.get('high_probability_filter')
        _require(isinstance(candidates,list), 'preflight candidates missing')
        if c2:
            _require([r['market'] for r in candidates]==list(WATCH_MARKETS), 'preflight wrong markets')
            ps=c2['goals']['markets']
            for row in candidates:
                market=row['market'];prob=row['p_model']
                _require(abs(prob-ps[market])<1e-8, 'preflight probability mismatch')
                _require(row.get('filter_state')==('IZLEME' if prob>=.75 else 'ELENDI_ESIK_ALTI')
                         and row.get('recommended') is False and row.get('A_B_C')=='DEGERLENDIRILEMEDI',
                         'preflight gate manipulated')
                baseline=row.get('base_rate',{})
                _require(baseline.get('prediction_model_input') is False and baseline.get('changes_filter') is False,
                         'base rate improperly changed filter')
            _require(dp.get('main_side_descriptive',{}).get('market')==max(SIDE,key=lambda k:ps[k])
                     and dp.get('main_general_descriptive',{}).get('market')==max(GENERAL,key=lambda k:ps[k]),
                     'preflight descriptive main selection mismatch')
        else:
            _require(candidates==[] and dp.get('main_side_descriptive') is None
                     and dp.get('main_general_descriptive') is None, 'preflight fallback from Model B')
        case_results.append({'case':i,'league':c['league'],'cutoff_exclusive':c['target_date'],
                             'canonical_c2':'CALCULATED_NOT_VALIDATED' if c2 else 'INSUFFICIENT_CONTEXT',
                             'model_b':'COMPARISON_ONLY' if b.get('probabilities') else 'INSUFFICIENT_CONTEXT',
                             'xg':xg['status'],
                             'first_half':analysis['other_markets']['first_half']['status'],
                             'corners':analysis['other_markets']['full_time_corners']['status'],
                             'real_fixture_verified':False,'bet_approved':False,
                             'watch_candidates':sum(r['filter_state']=='IZLEME' for r in candidates)})
    n_c2=sum(c['canonical_c2']=='CALCULATED_NOT_VALIDATED' for c in case_results)
    has_half=sum(c['first_half']=='EXPERIMENTAL_NOT_VALIDATED' for c in case_results)
    has_corners=sum(c['corners']=='EXPERIMENTAL_NOT_VALIDATED' for c in case_results)
    statuses={
      1:('KISMI','En yüksek olasılıklar yalnız açıklayıcı; onaylı A/B/C seçimi yok'),
      2:('KISMI','Dondurulmuş 4.413 maçın bütünlüğü kontrol edildi; maç günündeki güncellik kanıtlanmadı'),
      3:('CANLI_MAC_ASAMASI','Kullanıcının söylediği maçta resmî kaynak kontrolü yapılacak; toplu fikstür taraması yok'),
      4:('KISMI','Sonuç temelli form gösterildi; rakip-güçlü C3 henüz onaylı değil'),
      5:('CANLI_MAC_ASAMASI','Kadro ve kritik haberler analiz anında kontrol edilir; açıklanmamış ilk 11 engel değildir'),
      6:('KISMI',f'C2 {n_c2}/{len(case_results)} örnekte hesaplandı; C3 yalnız deneysel'),
      7:('AYRI_TUTULDU','Elo yardımcı unsur; hesapları değiştirmedi ve eski test tekrarlanmadı'),
      8:('KISMI','1X2 olasılıkları tutarlı, bağımsız ileri dönem kalibrasyonu yok'),
      9:('KISMI','C2 olan örneklerde gol/KG aynı olasılık dağılımından türetildi'),
      10:('KISMI',f'İlk yarı {has_half}/{len(case_results)} örnekte deneysel; doğru skorlar açıklayıcı'),
      11:('KISMI',f'Maç sonu korner {has_corners}/{len(case_results)} örnekte deneysel; ilk yarı korner yok'),
      12:('KISMI','§12.1 izleme filtresi ve §12.4 lig taban çizgisi hesaplandı; canlı A/B/C seçimi hâlâ kapalı'),
      13:('SONRA','Oran ve EV kullanıcı kararıyla sonraki aşamada'),
      14:('KISMI','Veri ve kalibrasyon uyarıları var; bağımsız ileri dönem doğrulaması yok'),
      15:('KISMI','Tekli/çoklu offline Markdown/JSON var; canlı maç raporu değil'),
      16:('SONRA','Değişmez maç önü tahmin defteri henüz başlatılmadı'),
      17:('SONRA','25 maçlık pilot henüz başlatılmadı'),
    }
    matrix=[{'number':i,'title':title,'status':statuses[i][0],'reason':statuses[i][1]}
            for i,title in enumerate(HEADINGS,1)]
    _require(len(matrix)==17 and len({m['number'] for m in matrix})==17,'section contract incomplete')
    return {'version':VERSION,'status':'PASS_OFFLINE_INTEGRATION_ONLY','live_263_accepted':False,
            'history_rows':src['rows'],'historical_sha256':src['sha256'],
            'tuesday_refresh_policy_confirmed':True,'automation_claimed':False,
            'count_of_sections':17,'sections':matrix,'cases':case_results,
            'c2_available_cases':n_c2,'blockers':list(BLOCKERS),
            'recommendation_count':0,'new_performance_backtest_performed':False}

def render(result):
    lines=['# 2.6.3 — 17 Bölümlük Bütünleşme Kabul Kapısı','',
           '**Durum: PASS_OFFLINE_INTEGRATION_ONLY. CANLI 2.6.3 ONAYI DEĞİLDİR.**',
           'Eski matematik ve xG karşılaştırma testleri tekrarlanmadı. Fikstür kodu değiştirilmedi.',
           f'Kaynak: {result["history_rows"]} maç; dondurulmuş SHA-256 `{result["historical_sha256"]}`.',
           '**Güncelleme günü: Salı (Europe/Istanbul). Otomasyon kanıtlanmadı.**','',
           '| Bölüm | Durum | Gerçek kanıt / eksik |','|---|---|---|']
    for s in result['sections']:
        lines.append(f'| {s["number"]}. {s["title"]} | {s["status"]} | {s["reason"]} |')
    lines+=['','## İncelenen örnekler','', '| Vaka | Lig | C2 | Mevcut B | xG |', '|---|---|---|---|---|']
    for c in result['cases']:
        lines.append(f'| {c["case"]} | {c["league"]} | {c["canonical_c2"]} | {c["model_b"]} | {c["xg"]} |')
    lines+=['','## Gerçek canlı kabulü bekleyen konular','']
    lines.extend('- '+b for b in result['blockers'])
    lines+=['','**Sonuç:** Offline 17-bölüm denetim kapısı geçti; bu, tam canlı analiz, tahmin güvenilirliği veya bahis tavsiyesi onayı değildir.','']
    return '\n'.join(lines)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args(argv)
    bundle=json.loads(Path(a.bundle).read_text(encoding='utf-8'))
    result=audit(bundle)
    dest=Path(a.out);dest.mkdir(exist_ok=True,parents=True)
    (dest/'section_acceptance_263.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (dest/'section_acceptance_263.md').write_text(render(result),encoding='utf-8')
    print(json.dumps({'status':result['status'],'sections':17,'cases':len(result['cases']),
                      'c2_available_cases':result['c2_available_cases'],
                      'live_263_accepted':False},ensure_ascii=False))
if __name__=='__main__':main()
