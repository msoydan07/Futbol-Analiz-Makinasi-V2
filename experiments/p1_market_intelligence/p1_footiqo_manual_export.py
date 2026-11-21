"""Strict offline adapter for Footiqo's officially *manually* exported CSV tables.

No network, scraping, automated exports, odds redistribution, or production writes.
Data is accepted as source-asserted closing odds, not timestamp-certified quotes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from p1_market import MARKETS, analyze_prices, score_observed, best_choices, MarketDataError

SCHEMA = 'P1_FOOTIQO_OFFLINE_MANUAL_EXPORT_AUDIT_V1'
ODDS_MAP = {
    'MS': {'MS1':'H','MSX':'D','MS2':'A'},
    'OU25': {'UNDER_2.5':'U25','OVER_2.5':'O25'},
    'KG': {'BTTS_YES':'BTTSY','BTTS_NO':'BTTSN'},
}
IDENTITY = ('id','matchDate','homeTeam','awayTeam','League','Season')
CUTOFF = date(2026, 11, 21)


def read_csv(path: Path) -> list[dict]:
    data = path.read_text(encoding='utf-8-sig')
    if not data.strip():
        raise ValueError('EMPTY_INPUT:' + path.name)
    try:
        dialect = csv.Sniffer().sniff(data[:8192], delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(data.splitlines(), dialect=dialect))
    if not rows:
        raise ValueError('NO_DATA_ROWS:' + path.name)
    return rows


def record_date(raw: str) -> date:
    raw=(raw or '').strip()
    for pattern in ('%d-%m-%y %H:%M','%d-%m-%Y %H:%M','%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M',
                    '%d/%m/%Y %H:%M','%Y-%m-%d','%d-%m-%y','%d-%m-%Y'):
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    raise ValueError('DATE_FORMAT_UNRECOGNIZED')


def clean_identity(r: dict) -> tuple:
    for k in IDENTITY:
        if not str(r.get(k) or '').strip():
            raise ValueError('IDENTITY_FIELD_MISSING:' + k)
    match_id=str(r['id']).strip()
    if not match_id.isdigit():
        raise ValueError('BAD_MATCH_ID')
    d=record_date(r['matchDate'])
    if d>CUTOFF:
        raise ValueError('FUTURE_FIXTURE')
    return (match_id, d.isoformat(), *(str(r[k]).strip().casefold() for k in ('homeTeam','awayTeam','League','Season')))


def goals(r: dict) -> tuple[int,int]:
    try:
        raw=(str(r['FTHG']).strip(),str(r['FTAG']).strip())
        if not all(v.isdigit() for v in raw):
            raise ValueError('NONINTEGER_FINAL_SCORE')
        g=tuple(int(v) for v in raw)
        if max(g)>40:
            raise ValueError('UNREALISTIC_FINAL_SCORE')
        claimed=str(r.get('FTR') or '').strip().upper()
        actual='H' if g[0]>g[1] else 'A' if g[0]<g[1] else 'D'
        if claimed and claimed != actual:
            raise ValueError('INCONSISTENT_FINAL_RESULT')
        return g
    except KeyError as e:
        raise ValueError('SCORE_FIELD_MISSING:'+str(e)) from e


def inspect(odds_csv: Path | list[Path], scores_csv: Path | list[Path], *, official_manual_export: bool,
            private_noncommercial_research: bool) -> dict:
    if official_manual_export is not True or private_noncommercial_research is not True:
        raise ValueError('MANUAL_EXPORT_AND_PRIVATE_NONCOMMERCIAL_ATTESTATION_REQUIRED')
    odds_files=[odds_csv] if isinstance(odds_csv,Path) else list(odds_csv)
    score_files=[scores_csv] if isinstance(scores_csv,Path) else list(scores_csv)
    if not odds_files or not score_files:
        raise ValueError('ODDS_AND_SCORES_FILES_REQUIRED')
    odds_rows=[row for path in odds_files for row in read_csv(path)]
    score_rows=[row for path in score_files for row in read_csv(path)]
    required_odds=set(IDENTITY) | set(v for market in ODDS_MAP.values() for v in market.values())
    required_scores=set(IDENTITY) | {'FTHG','FTAG'}
    if not required_odds <= set(odds_rows[0]):
        raise ValueError('ODDS_COLUMNS_MISSING:'+','.join(sorted(required_odds-set(odds_rows[0]))))
    if not required_scores <= set(score_rows[0]):
        raise ValueError('SCORE_COLUMNS_MISSING:'+','.join(sorted(required_scores-set(score_rows[0]))))

    sources={}
    bad_scores=Counter()
    for i,r in enumerate(score_rows,2):
        try:
            ident=clean_identity(r)
            if ident[0] in sources:
                raise ValueError('DUPLICATE_SCORE_ID')
            sources[ident[0]]=(ident, goals(r))
        except ValueError as e:
            bad_scores[str(e)]+=1
            # A duplicate score ID contaminates the join and must stop acceptance.
            if str(e)=='DUPLICATE_SCORE_ID':
                raise
    seen=set()
    rejected=Counter()
    accepted=[]
    max_margins={m:[] for m in ODDS_MAP}
    for i,row in enumerate(odds_rows,2):
        try:
            ident=clean_identity(row)
            mid=ident[0]
            if mid in seen:
                raise ValueError('DUPLICATE_ODDS_ID')
            seen.add(mid)
            if mid not in sources:
                raise ValueError('NO_MATCHING_SCORE_ID')
            score_identity, result=sources[mid]
            if ident!=score_identity:
                raise ValueError('SCORE_ODDS_IDENTITY_CONFLICT')
            prices={}
            for market,cols in ODDS_MAP.items():
                prices[market]={}
                for outcome,col in cols.items():
                    raw=(row.get(col) or '').strip().replace(',','.')
                    if not raw:
                        raise ValueError('INCOMPLETE_SEVEN_ODDS')
                    value=float(raw)
                    if not math.isfinite(value) or not 1.0<value<=1000:
                        raise ValueError('INVALID_PRICE')
                    prices[market][outcome]=value
                overround=sum(1/x for x in prices[market].values())
                if not 0.97<=overround<=1.4:
                    raise ValueError('UNUSUAL_MARKET_OVERROUND')
            calc=analyze_prices(prices)
            p0=score_observed(calc['p0'], *result)
            p1=score_observed(calc['p1']['p1_probabilities'], *result)
            sel0=calc['p0_select']['main']; sel1=calc['p1_select']['main']
            accepted.append({'date':ident[1],'league':row['League'].strip(), 'season':row['Season'].strip(),
                             'p0_brier':p0['macro_brier'],'p1_brier':p1['macro_brier'],
                             'p0_logloss':p0['macro_log_loss'],'p1_logloss':p1['macro_log_loss'],
                             'p0_hit':int(p0['truth'][sel0['family']]==sel0['choice']),
                             'p1_hit':int(p1['truth'][sel1['family']]==sel1['choice'])})
            for group in ODDS_MAP:
                max_margins[group].append(calc['margins'][group])
        except (ValueError, TypeError, KeyError, MarketDataError, OverflowError, ZeroDivisionError) as e:
            rejected[str(e)[:110]]+=1

    def metrics(group):
        if not group: return None
        return {'n':len(group),
                'p0_brier':round(statistics.fmean(x['p0_brier'] for x in group),6),
                'p1_brier':round(statistics.fmean(x['p1_brier'] for x in group),6),
                'p0_logloss':round(statistics.fmean(x['p0_logloss'] for x in group),6),
                'p1_logloss':round(statistics.fmean(x['p1_logloss'] for x in group),6),
                'p0_hits':sum(x['p0_hit'] for x in group),
                'p1_hits':sum(x['p1_hit'] for x in group)}
    dates=sorted(set(x['date'] for x in accepted))
    if len(dates)>=8 and len(accepted)>=200:
        cutoff=dates[int(.7*len(dates))]
        train=[x for x in accepted if x['date']<cutoff]
        holdout=[x for x in accepted if x['date']>=cutoff]
        split={'method':'CHRONOLOGY_ONLY_NO_CALIBRATION_FIT','cutoff':cutoff,
               'train':metrics(train),'test':metrics(holdout)}
    else:
        split={'status':'INSUFFICIENT_DISTINCT_DAYS_OR_MATCHES_FOR_TEMPORAL_HOLDOUT'}
    return {'schema':SCHEMA,'source':'Footiqo officially manually exported CSV tables',
            'source_url':'https://footiqo.com/database/',
            'terms_url':'https://footiqo.com/dataset-licence/',
            'bookmaker':'1xBet (publisher attribution, not separately verified)',
            'price_type':'PUBLISHER_DESCRIBED_CLOSING_ODDS','quote_timestamp_grade':'UNKNOWN_UNTIMED_SOURCE_ASSERTION',
            'no_web_automation':True,'private_noncommercial_research_only':True,
            'odds_files_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in odds_files},
            'scores_files_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in score_files},
            'odds_rows':len(odds_rows),'scores_rows':len(score_rows),
            'accepted':len(accepted),'excluded':len(odds_rows)-len(accepted),
            'reject_reasons':dict(rejected),'unusable_score_rows':dict(bad_scores),
            'leagues':dict(Counter(r['league'] for r in accepted)),
            'seasons':dict(Counter(r['season'] for r in accepted)),
            'p0_p1_descriptive':metrics(accepted),'chronology_holdout':split,
            'historical_outcome_is_not_live_asof_certified':True,
            'model_not_promoted':True,
            'raw_user_or_third_party_odds_not_in_aggregate':True}


def cli():
    p=argparse.ArgumentParser(description='Offline Footiqo manual CSV export adapter (no network)')
    p.add_argument('--odds',required=True,type=Path,nargs='+',help='One or more authorized manual Odds CSV exports')
    p.add_argument('--scores',required=True,type=Path,nargs='+',help='Matching manually exported Overview/Scores CSV files')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--attest-official-manual-export',action='store_true')
    p.add_argument('--attest-private-noncommercial-research',action='store_true')
    a=p.parse_args()
    report=inspect(a.odds,a.scores,
                   official_manual_export=a.attest_official_manual_export,
                   private_noncommercial_research=a.attest_private_noncommercial_research)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('research accepted=',report['accepted'],'excluded=',report['excluded'])

if __name__=='__main__':
    cli()
