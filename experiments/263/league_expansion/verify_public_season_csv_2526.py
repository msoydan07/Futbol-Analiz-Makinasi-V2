#!/usr/bin/env python3
"""Offline, read-only acceptance QA for independently downloaded 2025/26 CSV.
Swiss (CHE1) and Danish (DNK1) source: MatchDaySync public CSV exports.
Never fetch remote data, store original CSV in public GitHub, approve training,
or copy xG into research pool. Only aggregate QA may be publicly recorded.

Run: python verify_public_season_csv_2526.py --league CHE1 --csv /private/season.csv
     python verify_public_season_csv_2526.py --self-test
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
import io
import json
from pathlib import Path
import re
import unicodedata

# team, W, D, L, GF, GA, Pts (Swiss Football League / RSSSF 2025/26).
EXPECTED = {
    'CHE1': [
        ('Thun',24,3,11,80,52,75), ('St Gallen',20,10,8,72,47,70),
        ('Lugano',19,10,9,59,42,67), ('Sion',16,15,7,63,40,63),
        ('Basel',16,8,14,55,58,56), ('Young Boys',15,10,13,80,69,55),
        ('Luzern',14,11,13,76,66,53), ('Servette',13,14,11,71,63,53),
        ('Lausanne',11,9,18,53,67,42), ('Zurich',11,5,22,49,72,38),
        ('Grasshoppers',8,9,21,48,74,33), ('Winterthur',5,8,25,44,100,23)
    ],
    'DNK1': [
        ('AGF',19,10,3,62,32,67), ('Midtjylland',16,12,4,72,36,60),
        ('Nordsjaelland',15,5,12,51,46,50), ('Brondby',13,6,13,44,35,45),
        ('Viborg',13,5,14,49,51,44), ('Sonderjyske',12,8,12,44,49,44),
        ('Copenhagen',15,6,11,67,44,51), ('Odense',11,8,13,51,60,41),
        ('Silkeborg',10,6,16,41,67,36), ('Randers',9,8,15,33,47,35),
        ('Fredericia',9,7,16,45,68,34), ('Vejle',5,9,18,36,60,24)
    ]
}
ALIASES = {
    'CHE1': {
        'Thun':['FC Thun'], 'St Gallen':['FC St.Gallen 1879','St. Gallen','FC St Gallen','St Gallen 1879'],
        'Lugano':['FC Lugano'], 'Sion':['FC Sion'], 'Basel':['FC Basel','FC Basel 1893','Basel 1893'],
        'Young Boys':['BSC Young Boys','YB Young Boys'],
        'Luzern':['FC Luzern'], 'Servette':['Servette FC'],
        'Lausanne':['FC Lausanne-Sport','Lausanne-Sport'],
        'Zurich':['FC Zürich','FC Zurich','Zürich'],
        'Grasshoppers':['Grasshopper Club Zürich','Grasshopper Club Zurich','Grasshoppers Zürich'],
        'Winterthur':['FC Winterthur']
    },
    'DNK1': {
        'AGF':['Aarhus','Aarhus GF','AGF Aarhus'],
        'Midtjylland':['FC Midtjylland'], 'Nordsjaelland':['FC Nordsjælland','Nordsjælland','FC Nordsjaelland'],
        'Brondby':['Brøndby','Brøndby IF','Brondby IF'],
        'Viborg':['Viborg FF'], 'Sonderjyske':['SønderjyskE','Sønderjyske','SonderjyskE'],
        'Copenhagen':['FC Copenhagen','FC København','FC Kobenhavn','København'],
        'Odense':['OB','Odense BK','Odense Boldklub'],
        'Silkeborg':['Silkeborg IF'], 'Randers':['Randers FC'],
        'Fredericia':['FC Fredericia'], 'Vejle':['Vejle BK','Vejle Boldklub']
    }
}
REQUIRED = {'date','status','home','away','home_goals','away_goals'}


def norm(value: str) -> str:
    v = value.casefold().replace('ø','o').replace('æ','ae').replace('ß','ss').replace('œ','oe')
    v = ''.join(c for c in unicodedata.normalize('NFKD',v) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',re.sub('[^a-z0-9]',' ',v)).strip()


def name_map(league: str) -> dict[str,str]:
    d = {}
    for canonical, aliases in ALIASES[league].items():
        for a in [canonical] + aliases:
            key = norm(a)
            if key in d and d[key] != canonical:
                raise ValueError(f'Ambiguous alias {a}')
            d[key] = canonical
    return d


def csv_rows(source: str) -> list[dict]:
    # MatchDaySync CSV begins with one '# Source:' line; skip all leading comments.
    lines = source.splitlines()
    while lines and (not lines[0].strip() or lines[0].startswith('#')):
        lines.pop(0)
    reader = csv.DictReader(io.StringIO('\n'.join(lines)))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError('Missing required columns or CSV header')
    return list(reader)


def _score(value: str | None) -> int | None:
    # Missing score is never zero. Decimal, negative or spreadsheet formula rejected.
    if not isinstance(value,str) or not re.fullmatch(r'\d{1,2}',value.strip()):
        return None
    return int(value.strip())


def analyze(rows: list[dict], league: str) -> dict:
    if league not in EXPECTED:
        raise ValueError('Unknown league')
    target = {t[0]:t for t in EXPECTED[league]}
    canon = name_map(league)
    totals = defaultdict(lambda: [0,0,0,0,0,0,0])  # W,D,L,GF,GA,Pts,Played
    reasons = Counter()
    seen = set()
    raw_names = defaultdict(set)
    zero_zero = 0
    valid = 0
    for r in rows:
        status = str(r.get('status') or '').casefold().strip()
        if status not in ('finished','completed','ft','full-time','full time'):
            reasons['NOT_CONFIRMED_FINISHED'] += 1
            continue
        ds = str(r.get('date') or '')[:10]
        try:
            dt = date.fromisoformat(ds)
        except ValueError:
            reasons['INVALID_DATE'] += 1
            continue
        if not date(2025,7,1) <= dt <= date(2026,6,30):
            reasons['OUT_OF_SEASON'] += 1
            continue
        home, away = canon.get(norm(str(r.get('home') or ''))), canon.get(norm(str(r.get('away') or '')))
        if not home or not away or home == away:
            reasons['UNKNOWN_OR_SAME_TEAM'] += 1
            continue
        hg, ag = _score(r.get('home_goals')), _score(r.get('away_goals'))
        if hg is None or ag is None:
            reasons['INVALID_OR_MISSING_FULL_TIME_SCORE'] += 1
            continue
        key = (ds,home,away)
        if key in seen:
            reasons['DUPLICATE_CANONICAL_FIXTURE'] += 1
            continue
        seen.add(key)
        valid += 1
        raw_names[home].add(str(r['home']))
        raw_names[away].add(str(r['away']))
        zero_zero += int(hg == 0 and ag == 0)
        h, a = totals[home], totals[away]
        h[3] += hg; h[4] += ag; a[3] += ag; a[4] += hg
        h[6] += 1; a[6] += 1
        if hg > ag:
            h[0] += 1; h[5] += 3; a[2] += 1
        elif hg < ag:
            a[0] += 1; a[5] += 3; h[2] += 1
        else:
            h[1] += 1; a[1] += 1; h[5] += 1; a[5] += 1
    expected_count = {'CHE1':228,'DNK1':192}[league]
    mismatches = {}
    for team,(name,w,d,l,gf,ga,p) in target.items():
        actual = totals[team]
        expected = [w,d,l,gf,ga,p,w+d+l]
        if actual != expected:
            mismatches[team] = {'actual':actual,'expected':expected}
    covered = set(totals)
    extra = sorted(covered-set(target))
    passed = (valid == expected_count and len(rows) == expected_count and
              not reasons and not mismatches and not extra and
              len(covered) == 12)
    return {
        'scope':'OFFLINE_2025_26_SOURCE_ACCEPTANCE_RESEARCH_ONLY',
        'league':league, 'file_rows':len(rows), 'valid_unique_scored_rows':valid,
        'expected_valid_rows':expected_count,'unique_clubs':len(covered),
        'zero_zero_results':zero_zero,'raw_aliases_per_club':{k:sorted(v) for k,v in raw_names.items() if len(v)>1},
        'quarantine_reasons':dict(reasons), 'team_stat_mismatches':mismatches,
        'source_reconstructed_total_goals':sum(v[3] for v in totals.values()),
        'official_expected_total_goals':{'CHE1':750,'DNK1':595}[league],
        'score_and_coverage_gate':'PASS' if passed else 'FAIL_CLOSED',
        'rights_gate':'SEPARATE_REVIEW_REQUIRED_BEFORE_PUBLIC_DATA_REDISTRIBUTION',
        'trainable_rows_approved':0,'production_changes':False,
        'note':'Even PASS does not certify individual scores, legal rights, or deployment.'
    }


def self_test() -> None:
    assert norm('FC København') == 'fc kobenhavn'
    assert name_map('CHE1')[norm('FC Zürich')] == 'Zurich'
    assert name_map('DNK1')[norm('FC Copenhagen')] == 'Copenhagen'
    assert _score('0') == 0 and _score('') is None and _score('-1') is None
    src = '# Source: research-only\n' + 'date,status,home,away,home_goals,away_goals\n' + (
        '2025-08-08,finished,FC Thun,FC Sion,0,0\n'
        '2025-08-08,finished,Thun,Sion,0,0\n'
        '2025-08-08,scheduled,FC Basel,Servette,0,0\n'
    )
    out = analyze(csv_rows(src),'CHE1')
    assert out['valid_unique_scored_rows'] == 1 and out['zero_zero_results'] == 1
    assert out['quarantine_reasons'] == {'DUPLICATE_CANONICAL_FIXTURE':1,'NOT_CONFIRMED_FINISHED':1}
    assert out['score_and_coverage_gate'] == 'FAIL_CLOSED' and out['trainable_rows_approved'] == 0
    print('PASS synthetic: alias normalization, duplicate canonical fixture, real 0-0, missing/unfinished, fail closed')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--league',choices=sorted(EXPECTED))
    p.add_argument('--csv',help='A locally stored, rights-reviewed CSV. Never commit raw source.')
    p.add_argument('--report',help='Optional output path for aggregate-only JSON')
    p.add_argument('--self-test',action='store_true')
    opt = p.parse_args()
    if opt.self_test:
        self_test()
    else:
        if not opt.league or not opt.csv:
            p.error('--league and --csv required')
        report = analyze(csv_rows(Path(opt.csv).read_text(encoding='utf-8-sig')),opt.league)
        result = json.dumps(report,indent=2,ensure_ascii=False)+'\n'
        if opt.report:
            Path(opt.report).write_text(result,encoding='utf-8')
        print(result)
