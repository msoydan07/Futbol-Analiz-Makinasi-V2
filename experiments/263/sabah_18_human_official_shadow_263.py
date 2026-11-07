"""Assistant-reviewed official WEB fixture evidence for Nov 7 2026 (18 fixtures).

This is NOT machine-verified HTML, NOT a real pilot and NOT an odds intake.
Only manually inspected official league schedules, short-lived and only for
ephemeral model research. No permanent forward files or value bets.
"""
from __future__ import annotations
import argparse,json,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from collections import Counter
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from analyze_named_match_gate import run as named_gate
from forward_c3 import valid_gate,read_aware
from forward_quad import predict_quad_from_verified_gate
from forward_empirical_baseline_263 import produce
from four_model_value_policy_263 import decide
from market_fifth_baseline_263 import sealed_payload
from sabah_batch_263 import named
from sabah_today_scope_readonly_263 import summarize

DAY='2026-11-07'
REVIEWED='2026-11-07T10:10:00+00:00'
FROZEN='experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json'
HISTORY='data/quad_accepted_263/extended_history.csv'
BASE='m4_quad_base/historical_results.csv'
AUDIT='data/quad_accepted_263/source_acceptance.json'
M4LOCK='experiments/263/m4_lock.json'
DEV='experiments/263/forward_dev_calibration_lock_263.json'
TR=ZoneInfo('Europe/Istanbul')
SOURCES={
 'ENG2':'https://www.efl.com/match-centre/g2566958',
 'POR1':'https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada',
 'BEL1':'https://www.proleague.be/jpl-kalender!'
}
# Official fixture team names and absolute UEFA/UTC kick-off times read from
# each official authority's 7 November schedule. No guessing for other dates.
EVENTS=[
 ('ENG2','Wrexham','Wolverhampton Wanderers','12:30'),
 ('ENG2','Portsmouth','Stoke City','12:30'),
 ('ENG2','Bristol City','Norwich City','12:30'),
 ('ENG2','Preston North End','Southampton','15:00'),
 ('ENG2','Watford','Middlesbrough','15:00'),
 ('ENG2','Blackburn Rovers','West Ham United','15:00'),
 ('ENG2','Birmingham City','Swansea City','15:00'),
 ('ENG2','Charlton Athletic','Sheffield United','15:00'),
 ('ENG2','West Bromwich Albion','Millwall','15:00'),
 ('ENG2','Cardiff City','Burnley','15:00'),
 ('ENG2','Queens Park Rangers','Lincoln City','15:00'),
 ('POR1','CD Nacional','Académico','15:30'),
 ('POR1','FC Alverca','Casa Pia AC','18:00'),
 ('POR1','Sporting CP','Moreirense FC','20:30'),
 ('BEL1','KVC Westerlo','Sporting Charleroi','14:00'),
 ('BEL1','OH Leuven','KV Mechelen','16:15'),
 ('BEL1','Royal Antwerp FC','Lommel SK','18:45'),
 ('BEL1','RAAL La Louvière','Cercle Brugge','18:45')
]
REQUEST_NAMES={
 ('POR1','Nacional'):'CD Nacional',
 ('POR1','Alverca'):'FC Alverca',
 ('POR1','Casa Pia'):'Casa Pia AC',
 ('POR1','Moreirense'):'Moreirense FC',
 ('BEL1','Westerlo'):'KVC Westerlo',
 ('BEL1','Charleroi'):'Sporting Charleroi',
 ('BEL1','Royal Antwerp'):'Royal Antwerp FC',
 ('ENG2','QPR'):'Queens Park Rangers'
}
def observation(league,home,away,*,now,strict=True):
    if league not in SOURCES:raise ValueError('LEAGUE_NOT_REVIEWED')
    utc=now.astimezone(timezone.utc)
    review=datetime.fromisoformat(REVIEWED)
    if strict and not review<=utc<=review+timedelta(hours=1):
        raise ValueError('HUMAN_OFFICIAL_SCHEDULE_ATTESTATION_EXPIRED')
    matches=[x for x in EVENTS if x[0]==league and x[1]==home and x[2]==away]
    if len(matches)!=1:raise ValueError('PAIR_NOT_UNIQUELY_REVIEWED')
    tm=matches[0][3]
    ko=datetime.fromisoformat(DAY+'T'+tm+':00').replace(tzinfo=timezone.utc)
    if utc+timedelta(minutes=2)>=ko:raise ValueError('KICKOFF_ALREADY_TOO_CLOSE')
    return {'status':'VERIFIED_OFFICIAL_FIXTURE','home':home,'away':away,
            'match_date':DAY,'kickoff_utc':ko.isoformat(),
            'source_url':SOURCES[league],'retrieved_at_utc':REVIEWED,
            'source_origin':'HUMAN_WEB_OFFICIAL_ATTESTATION_NOT_MACHINE_REVERIFIED',
            'reviewed_at_utc':REVIEWED,
            'source_parser':'manual_official_web_review_nov7_2026',
            'source_independently_rechecked_in_runner':False}

def inspect():
    now=datetime.now(timezone.utc)
    if now.astimezone(TR).date().isoformat()!=DAY:
        raise ValueError('NOT_THE_REVIEWED_CALENDAR_DAY')
    all_names=named('legacy96',DAY,FROZEN)
    rows=[x for x in all_names if x['league'] in SOURCES]
    if len(rows)!=18 or Counter(x[0] for x in EVENTS)!={'ENG2':11,'POR1':3,'BEL1':4}:
        raise ValueError('REVIEWED_18_NOT_EXACT_44_COHORT')
    expected={(x['league'],x['home'],x['away']) for x in rows}
    resolved={}
    for row in rows:
        league=row['league']
        h=REQUEST_NAMES.get((league,row['home']),row['home'])
        a=REQUEST_NAMES.get((league,row['away']),row['away'])
        if (league,h,a) in resolved:raise ValueError('ALIAS_COLLISION')
        resolved[(league,h,a)]=row
    if set(resolved)!={(lg,h,a) for lg,h,a,_ in EVENTS}:
        raise ValueError('FIXTURE_REVIEW_MATCHES_NOT_THE_FROZEN_18')
    dev=json.loads(Path(DEV).read_text(encoding='utf-8'))
    out=[]
    with tempfile.TemporaryDirectory(prefix='263_manual_18_research_only_') as folder:
        for (league,home,away),original in resolved.items():
            row={**original,'evidence_scope':'HUMAN_WEB_OFFICIAL_ATTESTATION_NOT_MACHINE_REVERIFIED',
                 'source_url':SOURCES[league],'reviewed_at_utc':REVIEWED,
                 'model_status':'NOT_ATTEMPTED'}
            try:
                obs=observation(league,home,away,now=datetime.now(timezone.utc))
                row['kickoff_utc']=obs['kickoff_utc']
                gate=named_gate(league,home,away,lookup_override=lambda _h,_a:obs)
                if not isinstance(gate,dict) or gate.get('status')!='VERIFIED':
                    row['model_status']='BLOCKED_CANONICAL_ID'
                    row['reason']=gate.get('reason') if isinstance(gate,dict) else 'INVALID_GATE'
                    out.append(row);continue
                gate['human_web_attestation_not_machine_reverified']=True
                checked=datetime.now(timezone.utc)
                _,_,_,ko,_,_=valid_gate(gate,checked)
                path,f=predict_quad_from_verified_gate(
                    gate,HISTORY,Path(folder),M4LOCK,now=checked,base=BASE,source_audit=AUDIT)
                sealed_payload(f,'quad_forward_263_v1')
                b=produce(f,HISTORY,now=checked)
                d=decide(f,b,dev,observation=None,now=checked)
                if d.get('status')!='RESEARCH_PAS':raise ValueError('NO_ODDS_MUST_BE_PAS')
                result=summarize(f,d,'HUMAN_WEB_REVIEWED_OFFICIAL_SHADOW_ONLY_NO_PILOT')
                row.update(result)
                n=sum(x['status']=='AVAILABLE' for x in result['models'].values())
                row['model_available_count']=n
                row['model_status']='EXPERIMENTAL_PASS' if n>=3 and all(
                    result['models'][m]['status']=='AVAILABLE' for m in ('C3','M4')) else 'INSUFFICIENT_MODEL_CONTEXT'
            except (ValueError,TypeError,KeyError,OSError,AssertionError) as e:
                row['model_status']='BLOCKED_DATA_OR_SOURCE'
                row['reason']=type(e).__name__+':'+str(e)[:180]
            out.append(row)
    return {'schema':'263_NOV7_18_HUMAN_ATTESTED_OFFICIAL_NONPILOT_RESEARCH_V1',
            'day_turkey':DAY,'as_of_utc':now.isoformat(),
            'reviewed_at_utc':REVIEWED,'count':len(out),
            'source_provenance':'HUMAN_READ_FROM_OFFICIAL_WEB_TOOL_RESULTS_NOT_MACHINE_REVERIFIED',
            'official_web_references':SOURCES,
            'model_status_counts':dict(Counter(x['model_status'] for x in out)),
            'pilot_new100_records_created':0,'bookmaker_calls':0,
            'actual_official_html_reparsed_in_this_workflow':False,
            'permanent_forecast_files_created':0,
            'warning':'Not acceptable for machine-verified new100 sealed pilot or betting',
            'items':out}

def render(d):
    lines=['# 7 Kasım — Daha önce kaçan 18 maç (resmî sayfa insan incelemesi)','',
           '**İnsan tarafından resmî fikstür sayfası incelenmiş; GitHub HTML okuyucusu yeniden doğrulamamış.**',
           'Bu sayılar yalnız araştırma amaçlı; pilot defterine veya bahis önerisine dönüştürülmedi.','',
           '| TSİ | Lig | Maç | Kalibre MS yönü | 4 model | Durum |',
           '|---:|---|---|---|---:|---|']
    for x in sorted(d['items'],key=lambda a:a.get('kickoff_utc','9999')):
        ko=read_aware(x['kickoff_utc']).astimezone(TR).strftime('%H:%M') if x.get('kickoff_utc') else '?'
        ms=x.get('descriptive_top_calibrated_MS_market')
        value=ms['market']+' '+f'{ms["p"]*100:.1f}%' if ms and x.get('model_status')=='EXPERIMENTAL_PASS' else '—'
        lines.append('| '+ko+' | '+x['league']+' | '+x['home']+' – '+x['away']+' | '+
                     value+' | '+str(x.get('model_available_count','—'))+'/4 | '+
                     x['model_status']+' |')
    lines+=['','**Kaynak adresleri:**']
    for l,u in SOURCES.items():lines.append('- '+l+': '+u)
    lines+=['','Kaynak ispat türü: asistanın resmî web arama/okuma üzerinden yaptığı insan incelemesi; '
            'bu çalışmada GitHub HTML içeriği bağımsız tekrar doğrulanmamıştır.',
            'MS kalibre tek pazar yüzdesi 1/X/2 toplamı değildir; oran yok -> RESEARCH_PAS.']
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--mobile',required=True)
    a=p.parse_args();r=inspect()
    for path,content in [(a.out,json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n'),
                         (a.mobile,render(r))]:
        file=Path(path);file.parent.mkdir(parents=True,exist_ok=True)
        with file.open('x',encoding='utf-8') as f:f.write(content)
    print(json.dumps({'count':r['count'],'statuses':r['model_status_counts'],
                      'pilot':0,'odds':0,'source':'HUMAN_NOT_MACHINE_REVERIFIED'},ensure_ascii=False))
if __name__=='__main__':main()
