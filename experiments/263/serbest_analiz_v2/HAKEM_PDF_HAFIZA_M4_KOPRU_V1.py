#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only bridge: original iddaa PDF + verified Mobil V1.2 staging + archived M4/C3 V4.

Works on a local research copy or with a V4 model index exported from GitHub.
Does NOT train/change/fabricate M4 models or create original pre-match seals.

python HAKEM_PDF_HAFIZA_M4_KOPRU_V1.py --staging mobil_hakem_aktarim_v1_2.json \
  --pdf 21.11-almanya.pdf --models m4_fixture_index.json \
  --rule hakem_karar_kurali_v1.json --out-dir out

For future fixtures, if the M4 repository is available locally, replace
--models with --m4-root /path/to/Futbol-Analiz-Makinasi-V2. It discovers
committed V4 batch forecasts, decision files and verifies both payload SHAs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path
import unicodedata

from HAKEM_KARAR_UYGULA_V1 import EVENTS, validate as validate_prob, load_weights, choose
from MOBIL_HAKEM_STAGING_DOGRULAYICI_V1 import validate as verify_mobile

TR = timezone(timedelta(hours=3))
EVENTS = tuple(EVENTS)
MONTHS = {"oca":1,"sub":2,"mar":3,"nis":4,"may":5,"haz":6,"tem":7,"agu":8,"eyl":9,"eki":10,"kas":11,"ara":12}
ALIASES = {
    "b leverkusen":"leverkusen","bayer 04 leverkusen":"leverkusen", "bayer leverkusen":"leverkusen",
    "b dortmund":"dortmund","borussia dortmund":"dortmund",
    "borussia monchengladbach":"monchengladbach","monchenglad":"monchengladbach",
    "eintracht fran":"frankfurt","eintracht frankfurt":"frankfurt",
    "sport club freiburg":"freiburg","sportclub freiburg":"freiburg", "sc freiburg":"freiburg",
    "sv elversberg":"elversberg", "fc schalke 04":"schalke", "schalke 04":"schalke",
    "vfb stuttgart":"stuttgart", "tsg hoffenheim":"hoffenheim",
    "sc paderborn 07":"paderborn", "paderborn 07":"paderborn",
    "1 fc union berlin":"union berlin", "fc union berlin":"union berlin",
    "rb leipzig":"leipzig", "b monchengladbach":"monchengladbach",
    "paris saint germain":"psg", "manchester city":"manchester city",
    "man city":"manchester city", "man utd":"manchester united",
    "losc":"lille", "as monaco":"monaco", "rc lens":"lens",
    "olympique lyonnais":"lyon", "fc groningen":"groningen",
    "feyenoord rotterdam":"feyenoord", "excelsior rotterdam":"excelsior",
    "borussia m gladbach":"monchengladbach", "gladbach":"monchengladbach",
}

class BridgeError(ValueError):
    pass


def digest_object(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
        separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()


def name(s):
    s=str(s).replace('ı','i').replace('İ','I').replace('…',' ')
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',s)).strip()


def team(s):
    x=name(s)
    if x in ALIASES: return ALIASES[x]
    if x.startswith('fc ') and x[3:] in ALIASES: return ALIASES[x[3:]]
    if x.startswith('sc ') and x[3:] in ALIASES: return ALIASES[x[3:]]
    return x


def split_match(match):
    parts=re.split(r'\s+[-–—]\s*|\s*[-–—]\s+',str(match),maxsplit=1)
    if len(parts)!=2 or not all(s.strip() for s in parts):
        raise BridgeError('PDF_MATCH_NAME_CANNOT_SPLIT:'+str(match))
    return tuple(parts)


def time_utc(x):
    try:
        t=datetime.fromisoformat(str(x).replace('Z','+00:00'))
        if t.tzinfo is None:raise ValueError()
        return t.astimezone(timezone.utc)
    except Exception as e:
        raise BridgeError('AWARE_UTC_TIMESTAMP_REQUIRED') from e


def pdf_rows(pdf_bytes):
    """Independent rigid parser for 13-price iddaa table; reject unsupported layouts."""
    try: import fitz
    except ImportError as e: raise BridgeError('PYMUPDF_REQUIRED_FOR_PDF_INDEPENDENT_AUDIT') from e
    doc=fitz.open(stream=pdf_bytes,filetype='pdf')
    texts=[page.get_text() for page in doc]
    full='\n'.join(texts)
    if not full.strip(): raise BridgeError('PDF_NO_SEARCHABLE_TEXT')
    # Header day/month, NOT reliable as a year or independently authenticated kickoff.
    clean=name(full)
    dates=set()
    for mm in re.finditer(r'(?<!\d)(\d{1,2})\s+(oca|sub|mar|nis|may|haz|tem|agu|eyl|eki|kas|ara)(?![a-z])',clean):
        day=int(mm.group(1));month=MONTHS[mm.group(2)]
        if 1<=day<=31:dates.add((day,month))
    rowtexts=[]
    for t in texts:
        # Quoted football odds occur in a CANLI + 13 decimal numbers visual row.
        matches=list(re.finditer(r'(?m)^CANLI\s*\n',t))
        for i,m in enumerate(matches):
            nxt=matches[i+1].start() if i+1<len(matches) else len(t)
            frag=t[m.end():nxt]
            frag=re.split(r'\n(?=[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ ]{5,}\n(?:Bugün|Yarın|Dün))',frag,maxsplit=1)[0]
            # Before next row's CANLI, remove the trailing solitary '1' prefix.
            # Prices are exactly 13 decimal numbers when this PDF structure fits.
            odds=re.findall(r'(?<![\d])\d{1,3}\.\d{1,3}(?!\d)',frag)
            if len(odds)!=13:
                raise BridgeError('PDF_13_ODDS_ROW_NOT_CONFIRMED: row '+str(len(rowtexts)+1)+' found '+str(len(odds)))
            vals=[float(v) for v in odds]
            # PDF columns: 1 X 2; half-time; handicap; ALT UST VAR YOK.
            v=[vals[0],vals[1],vals[2],vals[10],vals[9],vals[11],vals[12]]
            rowtexts.append(dict(zip(EVENTS,v)))
    if not rowtexts: raise BridgeError('PDF_NO_VERIFIED_13_ODDS_ROWS')
    return rowtexts,dates



def independent_pdf_fixture_rows(pdf_bytes):
    """Extract printed time+match metadata separately from the 13-price table.

    Reject layouts for which row-wise correspondence cannot be established.
    This deliberately compares the labels that the bookmaker PDF actually
    contains; it is NOT official fixture-ID or source-server attestation.
    """
    try:
        import fitz
    except ImportError as e:
        raise BridgeError('PYMUPDF_REQUIRED_FOR_PDF_FIXTURE_VERIFICATION') from e
    doc=fitz.open(stream=pdf_bytes,filetype='pdf')
    full='\n'.join(page.get_text() for page in doc)
    pattern=r'(?m)^([0-2]\d:[0-5]\d)\s*\n([^\n]{3,120}[-–—][^\n]{2,120})\s*\n\+\s*\n\d{2,8}\s*$'
    found=re.findall(pattern,full)
    if not found:
        raise BridgeError('PDF_FIXTURE_NAMES_AND_TIMES_NOT_EXTRACTABLE')
    return [{'kickoff_time':hhmm,'match_label':label.strip()} for hhmm,label in found]

def _display_label_identity(value):
    # PDF selectable text sometimes inserts spaces within Turkish letters.
    # Only source-to-source exact character equivalence after white-space
    # repair is allowed, never fuzzy approximate fixture matching.
    return name(value).replace(' ','')


def audit_full_hafiza(staging, archive_path, expected_sha256=None):
    """Independent reconstruction of mobile V1.2 historical neighbor counts.

    Strictly GECMIS matches only. The official 2026/27 heldout outcomes cannot
    be included. Explicit archive hash can be pinned by the frozen referee rule.
    This is optional because mobile exports do not ship 9.3 MB raw archive.
    """
    archive_path=Path(archive_path)
    raw=archive_path.read_bytes()
    actual_sha=hashlib.sha256(raw).hexdigest()
    if expected_sha256 and actual_sha!=expected_sha256:
        raise BridgeError('FULL_HAFIZA_ARCHIVE_SHA_MISMATCH')
    archive=json.loads(raw)
    if archive.get('schema')!='ORAN_HAFIZASI_MOBIL_TAM_V1':
        raise BridgeError('UNSUPPORTED_HAFIZA_ARCHIVE_SCHEMA')
    if archive.get('count')!=len(archive.get('matches',[])):
        raise BridgeError('HAKEM_ARCHIVE_COUNT_INVALID')
    if staging.get('archive_total_matches')!=archive['count']:
        raise BridgeError('STAGING_ARCHIVE_TOTAL_DISAGREES')
    hist=[]
    for x in archive['matches']:
        if x.get('split')!='GECMIS' or x.get('s'):continue
        if len(x.get('p',[]))!=7 or len(x.get('score',[]))!=2:
            raise BridgeError('HAFIZA_HISTORY_ROW_INVALID')
        hist.append(x)
    if not hist or any(r.get('hafiza_eligible_n')!=len(hist) for r in staging['records']):
        raise BridgeError('HAFIZA_ELIGIBLE_SET_DISAGREES')
    radii=(.02,.03,.04,.05,.06,.08,.10)
    checked=0
    for r in staging['records']:
        q=[float(r['p0_seven_proportional'][k]) for k in EVENTS]
        # Stay in input order, no nearest-neighbor approximate search.
        distances=[]
        for x in hist:
            d=max(abs(float(a)-b) for a,b in zip(x['p'],q))
            distances.append(d)
        for rad in radii:
            ids=[i for i,d in enumerate(distances) if d<=rad+1e-12]
            if len(ids)>=100 or rad==radii[-1]:break
        if r.get('hafiza_similar_n')!=len(ids):
            raise BridgeError('HAFIZA_RAW_ARCHIVE_NEIGHBOR_COUNT_MISMATCH:'+r['match_name_pdf'])
        if abs(float(r.get('hafiza_radius_pp',-1))-rad*100)>.001:
            raise BridgeError('HAFIZA_RAW_ARCHIVE_RADIUS_MISMATCH:'+r['match_name_pdf'])
        h=[0]*7
        for idx in ids:
            home,away=hist[idx]['score'];y=(int(home>away),int(home==away),int(home<away),
                int(home+away>=3),int(home+away<=2),int(home>0 and away>0),
                int(home==0 or away==0))
            h=[a+b for a,b in zip(h,y)]
        observed=[r['hafiza_event_counts'][k] for k in EVENTS]
        if h!=observed:raise BridgeError('HAFIZA_RAW_ARCHIVE_EVENT_COUNTS_MISMATCH:'+r['match_name_pdf'])
        checked+=1
    return {'archive_sha256':actual_sha,'checked_matches':checked,'eligible_historical':len(hist),
            'status':'COMPLETE_RAW_ARCHIVE_RECONSTRUCTION_MATCHES_MOBILE'}

def read_model_index(path):
    doc=json.loads(Path(path).read_text(encoding='utf-8'))
    if doc.get('schema') not in ('M4_C3_V4_50_PREMATCH_INDEX_V1','HAKEM_M4_V4_SOURCE_ONLY_V1'):
        raise BridgeError('UNSUPPORTED_MODEL_INDEX_SCHEMA')
    out=[]
    for r in doc.get('records',[]):
        p=validate_prob(r['seven_calibrated_v4'])
        ko=time_utc(r['kickoff_utc'])
        if not isinstance(r.get('forecast_sha256'),str) or len(r['forecast_sha256'])!=64:
            raise BridgeError('M4_SOURCE_SHA_MISSING')
        out.append({'home':r['home'],'away':r['away'],'league':r['league'],
            'kickoff_utc':r['kickoff_utc'], 'predicted':p,
            'model_source':'ARCHIVE_INDEX_WITH_SHA_REFERENCES',
            'forecast_sha256':r['forecast_sha256'],
            'decision_sha256':r['decision_sha256'],
            'fixture_key':(r['league'],r['kickoff_utc'],team(r['home']),team(r['away']))})
    if not out:raise BridgeError('MODEL_INDEX_NO_ROWS')
    return out


def read_model_repo(root):
    root=Path(root);reports=list((root/'experiments/263/sabah_batch_reports').glob('new100_*.json'))
    if not reports:raise BridgeError('M4_REPO_BATCH_REPORTS_NOT_FOUND')
    out=[];seen=set()
    for path in reports:
        doc=json.loads(path.read_text(encoding='utf-8'))
        for match in doc.get('outcomes',[]):
            fpath=match.get('forecast_path')
            if not fpath:continue
            if not re.fullmatch(r'forward_morning_263/\d{4}-\d{2}-\d{2}/[0-9a-f]{24}\.json',fpath):
                raise BridgeError('UNSAFE_FORECAST_PATH')
            filename=fpath.rsplit('/',1)[-1].removesuffix('.json')
            day=fpath.split('/')[1]
            decision_path=root/'experiments/263/sabah_research/new100'/day/filename/'decision.json'
            forecast_path=root/fpath
            if not decision_path.is_file() or not forecast_path.is_file():continue
            forecast=json.loads(forecast_path.read_text(encoding='utf-8'))
            decision=json.loads(decision_path.read_text(encoding='utf-8'))
            if decision.get('selection_policy_version')!='20261121_C3_2025_FROZEN_V4':continue
            for payload in (forecast,decision):
                if payload.get('payload_sha256')!=digest_object({k:v for k,v in payload.items() if k!='payload_sha256'}):
                    raise BridgeError('M4_DECISION_OR_FORECAST_FILE_TAMPERED')
            if (forecast['payload_sha256']!=match['forecast_sha256'] or
                decision['payload_sha256']!=match['decision_sha256'] or
                decision['forecast_sha256']!=forecast['payload_sha256']):
                raise BridgeError('M4_BATCH_RECORDED_SHA_MISMATCH')
            if time_utc(forecast['created_at_utc']) >=time_utc(match['kickoff_utc']):
                raise BridgeError('M4_FORECAST_CREATED_AFTER_KICKOFF')
            probs={x['market']:x['calibrated_probability'] for x in decision['model_market_diagnostics']}
            p=validate_prob(probs)
            fixture=forecast['fixture']
            if (fixture['kickoff_utc']!=match['kickoff_utc'] or fixture['league']!=match['league']):
                raise BridgeError('M4_FIXTURE_MISMATCH')
            unique=(match['league'], match['kickoff_utc'],team(match['home']),team(match['away']))
            if unique in seen:continue
            seen.add(unique)
            out.append({'home':match['home'],'away':match['away'],'league':match['league'],
                'kickoff_utc':match['kickoff_utc'],'predicted':p,
                'model_source':'EXACT_ARCHIVED_FORECAST_AND_DECISION_SHA_VERIFIED',
                'forecast_sha256':forecast['payload_sha256'],'decision_sha256':decision['payload_sha256'],
                'fixture_key':unique})
    if not out:raise BridgeError('REPO_NO_FROZEN_V4_MATCHES')
    return out


def identify(row, candidates, date_of_match, pdf_day_month):
    h,a=split_match(row['match_name_pdf'])
    hp,ap=team(h),team(a)
    t=row['kickoff_local_time_user_label']
    possible=[]
    for c in candidates:
        kickoff=time_utc(c['kickoff_utc']).astimezone(TR)
        if kickoff.strftime('%H:%M')!=t:continue
        if date_of_match is not None and kickoff.date().isoformat()!=date_of_match:continue
        if pdf_day_month and (kickoff.day,kickoff.month) not in pdf_day_month:continue
        if row.get('league_code_user_label') and c['league']!=row['league_code_user_label']:continue
        ch,ca=team(c['home']),team(c['away'])
        if hp==ch and ap==ca: possible.append(c)
    if len(possible)==1:return possible[0]
    if len(possible)>1:raise BridgeError('AMBIGUOUS_M4_FIXTURE_MATCH:'+row['match_name_pdf'])
    # Fail-closed: no alternate team or rotated home/away guesses.
    raise BridgeError('M4_FIXTURE_NOT_FOUND_OR_ALIAS_REVIEW_REQUIRED:'+row['match_name_pdf'])


def integrate(staging_file,pdf_file,rule_file,model_index=None,repo_root=None,date_of_match=None,full_archive=None):
    if bool(model_index)==bool(repo_root):raise BridgeError('PROVIDE_EXACTLY_ONE_MODEL_SOURCE')
    if date_of_match is not None:
        datetime.strptime(date_of_match,'%Y-%m-%d')
    raw_pdf=Path(pdf_file).read_bytes()
    staging=json.loads(Path(staging_file).read_text(encoding='utf-8'))
    verify_mobile(staging,raw_pdf)
    if staging.get('history_test_included') is not False:
        raise BridgeError('HAFIZA_TEST_ROWS_CANNOT_ENTER_REFEREE_MEMORY')
    if any(r.get('history_test_included') is not False for r in staging['records']):
        raise BridgeError('INDIVIDUAL_MEMORY_TEST_ROWS_MUST_BE_EXCLUDED')
    odds_rows,date_labels=pdf_rows(raw_pdf)
    fixtures=independent_pdf_fixture_rows(raw_pdf)
    rows=staging['records']
    if len(odds_rows)!=len(rows):raise BridgeError('PDF_STAGING_ROW_COUNT_MISMATCH')
    if len(fixtures)!=len(odds_rows):raise BridgeError('PDF_FIXTURE_ODDS_ROW_COUNT_MISMATCH')
    # Critical guard: verifying PDF SHA + raw odds is NOT sufficient to prove
    # which named fixture each odds row belongs to. Verify names and time too.
    for i,(fixture,r) in enumerate(zip(fixtures,rows),1):
        if (fixture['kickoff_time']!=r['kickoff_local_time_user_label']
            or _display_label_identity(fixture['match_label'])!=_display_label_identity(r['match_name_pdf'])):
            raise BridgeError('PDF_FIXTURE_NAME_OR_TIME_MISMATCH_ROW_'+str(i))
    for i,(proof,r) in enumerate(zip(odds_rows,rows),1):
        if any(abs(proof[k]-float(r['seven_raw_odds'][k]))>1e-9 for k in EVENTS):
            raise BridgeError('PDF_SEVEN_ODDS_DISAGREE_WITH_MOBILE_ROW_'+str(i))
        if any(k in r for k in ('score','final_score','actual_result','final_result')):
            raise BridgeError('MOBILE_RESULT_LEAKAGE_FORBIDDEN')
    models=read_model_index(model_index) if model_index else read_model_repo(repo_root)
    weights,policy=load_weights(rule_file)
    archive_audit=(audit_full_hafiza(staging,full_archive,policy.get('source_sha256'))
                   if full_archive is not None else None)
    seen=set();decisions=[]
    for r in rows:
        match=identify(r,models,date_of_match,date_labels)
        key=match['fixture_key']
        if key in seen:raise BridgeError('DUPLICATE_MODEL_FIXTURE_USED')
        seen.add(key)
        experts={'M4_C3_V4':match['predicted'],'P0':validate_prob(r['p0_seven_proportional']),
            'HAFIZA':validate_prob(r['hafiza_seven_realized'])}
        outcome=choose(experts,weights)
        selected=outcome['ana_tercih']
        source_preference={src:max(EVENTS,key=lambda k:experts[src][k]) for src in experts}
        support_count=sum(event==selected for event in source_preference.values())
        agreement_range=100*(max(experts[src][selected] for src in experts)
                             -min(experts[src][selected] for src in experts))
        agreement={'status':'DESCRIPTIVE_NOT_CALIBRATED_CONFIDENCE',
                   'top_event_support_count':support_count,
                   'selected_event_prob_spread_pp':round(agreement_range,2),
                   'expert_top_events':source_preference,
                   'warning':'P0 ve Hafiza ayni oran girdilerini kullandigindan bagimsiz oy degildir.'}
        now=time_utc(staging['generated_at_utc_client_clock'])
        ko=time_utc(match['kickoff_utc'])
        classification=('RETROSPECTIVE_EXPORT_AFTER_KICKOFF' if now>=ko else
            'CLIENT_CLOCK_BEFORE_KICKOFF_NOT_INDEPENDENT_SEAL')
        decisions.append({'match':r['match_name_pdf'],'official_match':match['home']+' - '+match['away'],
            'league':match['league'],'kickoff_utc':match['kickoff_utc'],
            'export_utc_client_clock':staging['generated_at_utc_client_clock'],
            'classification':classification,'M4_forecast_sha256':match['forecast_sha256'],
            'M4_decision_sha256':match['decision_sha256'],'M4_source_status':match['model_source'],
            'mobile_hafiza_neighbors':r['hafiza_similar_n'],'seven_experts':experts,
            'decision':outcome,'uyum_gostergesi':agreement})
    final={'schema':'HAKEM_V1_M4_PDF_HAFIZA_BRIDGE_V1',
        'status':'READ_ONLY_RESEARCH_DECISIONS_NOT_ORIGINAL_PREMATCH_SEALS',
        'model_count_available':len(models),'match_count':len(decisions),'pdf_sha256':hashlib.sha256(raw_pdf).hexdigest(),
        'mobile_payload_sha256':staging['staging_payload_sha256'],
        'full_memory_independent_audit':archive_audit if archive_audit else {'status':'NOT_CHECKED_RAW_ARCHIVE_NOT_SUPPLIED'},
        'referee_training_scope':policy.get('scope'),
        'scope':'USER_PDF_7_PRICES_AND_FIXTURE_LABELS_PLUS_MOBILE_HISTORY_PLUS_M4_V4',
        'pdf_odds_independently_checked':len(rows)*7,
        'pdf_fixture_labels_independently_checked':len(fixtures),
        'warnings':['Hakem yuzdeleri tarihsel agirlilikli arastirma ciktisidir, kazanma garantisi degildir.',
                    'M4 endeksi kullanildiysa SHA referanslari indeks uzerinden gelir; kaynak karar/forecast dosyalari bu kosuda tekrar acilmamis olabilir.',
                    'Mobil aktarim kayitlari client clock ve sonradan aktarim oldugu icin kendiliginden pre-match muhur degildir.',
                    'Hakem ogrenme kurali 2026/27 arastirma verilerini daha once gormustur; bu yeni kor test degildir.',
                    'Bahis karliligi veya canli isabet kaniti yoktur.'],
        'decisions':decisions}
    final['payload_sha256']=digest_object(final)
    return final


def format_markdown(doc):
    out=['# Karar Hakemi V1 — PDF + Hafıza + M4/C3 entegrasyon raporu','',
       f"Doğrulanan maç: **{doc['match_count']}** | PDF oranı: **{doc['pdf_odds_independently_checked']}** | Durum: araştırma",'',
       '| Maç | M4/C3 | P0 | Hafıza | Hakem ana kararı | Alternatif |','|---|---:|---:|---:|---|---|']
    for r in doc['decisions']:
        d=r['decision'];k=d['ana_tercih'];a=d['alternatif_tercih']
        out.append('| '+r['match'].replace('|','/')+' | '+
          '%.1f%%'%(100*r['seven_experts']['M4_C3_V4'][k])+' | '+
          '%.1f%%'%(100*r['seven_experts']['P0'][k])+' | '+
          '%.1f%%'%(100*r['seven_experts']['HAFIZA'][k])+' | '+
          d['ana_tercih_tr']+' **%'+f"{d['hakem_arastirma_yuzdesi']:.2f}"+'** | '+
          d['alternatif_tr']+' %'+f"{d['alternatif_yuzdesi']:.2f}"+' |')
    out+=['','**Not:** Üç yüzde, Hakem’in seçtiği *aynı olay* içindir. Alternatif farklı pazar ailesindendir.',
           '**Provenans:** '+'; '.join(sorted(set(r['classification'] for r in doc['decisions']))),
           '**Sınırlama:** Geriye dönük mobil aktarım maç önü üçlü mühür değildir. Hakem yüzdeleri bağımsız kalibre edilmiş kazanma olasılığı olarak yorumlanmamalıdır.',
           '','## Kaynak bütünlüğü',
           '- PDF SHA-256: `'+doc['pdf_sha256']+'`',
           '- Mobil aktarım SHA-256: `'+doc['mobile_payload_sha256']+'`',
           '- Karar çıktısı SHA-256: `'+doc['payload_sha256']+'`','']
    return '\n'.join(out)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--staging',required=True,type=Path)
    ap.add_argument('--pdf',required=True,type=Path)
    ap.add_argument('--rule',required=True,type=Path)
    m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--models',type=Path)
    m.add_argument('--m4-root',type=Path)
    ap.add_argument('--match-date',help='Optional explicit local ISO date for ambiguity control')
    ap.add_argument('--out-dir',required=True,type=Path)
    ap.add_argument('--memory-full',type=Path,help='Optional original 35,938-match raw archive for independent Hafiza verification')
    a=ap.parse_args()
    try:doc=integrate(a.staging,a.pdf,a.rule,model_index=a.models,repo_root=a.m4_root,date_of_match=a.match_date,full_archive=a.memory_full)
    except (BridgeError,ValueError,OSError,KeyError) as e: ap.exit(2,'BLOCKED: '+str(e)+'\n')
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'HAKEM_BAGLI_KARARLAR.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (a.out_dir/'HAKEM_BAGLI_TEK_RAPOR.md').write_text(format_markdown(doc),encoding='utf-8')
    print(json.dumps({'status':doc['status'],'matches':doc['match_count'],
       'independent_pdf_prices':doc['pdf_odds_independently_checked'],
       'decisions':[{'match':r['match'],'main':r['decision']['ana_tercih_tr'],
           'pct':r['decision']['hakem_arastirma_yuzdesi']} for r in doc['decisions']]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
