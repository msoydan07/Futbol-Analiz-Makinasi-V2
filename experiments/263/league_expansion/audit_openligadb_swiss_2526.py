#!/usr/bin/env python3
"""Research-only OpenLigaDB Swiss Super League 2025/26 score quality gate.

Input: a single, explicitly supplied JSON export of
  https://api.openligadb.de/getmatchdata/bsl/2025
No network requests, no mutation, no model training and no merge into CC0 data.
Attribution: Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

EXPECTED_LEAGUE_ID = 4902
EXPECTED_SCORED_MATCHES = 228  # 12 clubs x 38 / 2; quality heuristic, NOT proof
MIN_DATE = date(2025, 7, 1)
MAX_DATE = date(2026, 6, 30)


def _local_day(match: dict) -> date | None:
    utc = match.get('matchDateTimeUTC')
    local = match.get('matchDateTime')
    try:
        if isinstance(utc, str) and utc:
            stamp = datetime.fromisoformat(utc.replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                return None  # do not silently assume timezone
            return stamp.astimezone(ZoneInfo('Europe/Zurich')).date()
        if isinstance(local, str) and local:
            return datetime.fromisoformat(local).date()
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def _final_result(match: dict) -> tuple[int, int] | None:
    """Exact after-90-minutes result; do not use last entry or highest order."""
    results = match.get('matchResults')
    if not isinstance(results, list):
        return None
    candidates = []
    for r in results:
        if not isinstance(r, dict):
            continue
        kind = r.get('resultTypeID', r.get('resultTypeId'))
        name = str(r.get('resultName') or '').strip().casefold()
        is_ft = kind == 2 or (kind is None and name in ('endergebnis', 'full-time', 'full time'))
        if not is_ft:
            continue
        h, a = r.get('pointsTeam1'), r.get('pointsTeam2')
        if type(h) is not int or type(a) is not int or not (0 <= h <= 30 and 0 <= a <= 30):
            return None
        candidates.append((h, a))
    return candidates[0] if len(candidates) == 1 else None


def analyze(records: list[dict]) -> dict:
    if not isinstance(records, list):
        raise ValueError('Expected OpenLigaDB API JSON array, not object')
    accepted_keys: set[tuple] = set()
    seen_match_ids: set[int] = set()
    score_dist = Counter()
    reasons = Counter()
    clean: list[dict] = []
    quarantined: list[dict] = []
    unfinished = 0
    for idx, m in enumerate(records):
        if not isinstance(m, dict):
            quarantined.append({'index': idx, 'reason': 'INVALID_MATCH_SHAPE'})
            reasons['INVALID_MATCH_SHAPE'] += 1
            continue
        match_id = m.get('matchID', m.get('matchId'))
        d = _local_day(m)
        home = m.get('team1') or {}
        away = m.get('team2') or {}
        t1 = home.get('teamId') if isinstance(home, dict) else None
        t2 = away.get('teamId') if isinstance(away, dict) else None
        league_id = m.get('leagueId', m.get('leagueID'))
        why = None
        if league_id != EXPECTED_LEAGUE_ID:
            why = 'WRONG_LEAGUE'
        elif type(match_id) is not int or match_id in seen_match_ids:
            why = 'DUPLICATE_OR_MISSING_MATCH_ID'
        elif d is None:
            why = 'INVALID_MATCH_DATE'
        elif d < MIN_DATE or d > MAX_DATE:
            why = 'OUTSIDE_2025_26_SEASON'
        elif type(t1) is not int or type(t2) is not int or t1 == t2:
            why = 'INVALID_TEAM_IDENTITIES'
        elif m.get('matchIsFinished') is not True:
            unfinished += 1
            seen_match_ids.add(match_id)
            continue
        if why is not None:
            quarantined.append({'index': idx, 'match_id': match_id, 'date': d.isoformat() if d else None, 'reason': why})
            reasons[why] += 1
            continue
        seen_match_ids.add(match_id)
        ft = _final_result(m)
        if ft is None:
            why = 'NO_UNAMBIGUOUS_FT_SCORE'
        else:
            key = (d.isoformat(), t1, t2)
            if key in accepted_keys:
                why = 'DUPLICATE_FIXTURE_IDENTITY'
        if why is not None:
            quarantined.append({'index': idx, 'match_id': match_id, 'date': d.isoformat(), 'reason': why})
            reasons[why] += 1
            continue
        accepted_keys.add(key)
        score_dist[f'{ft[0]}-{ft[1]}'] += 1
        clean.append({'match_id': match_id, 'date': d.isoformat(), 'home_id': t1, 'away_id': t2,
                      'home_goals': ft[0], 'away_goals': ft[1]})
    n = len(clean)
    return {
        'source': 'OpenLigaDB', 'league': 'CHE1', 'season': '2025-26',
        'source_endpoint': 'https://api.openligadb.de/getmatchdata/bsl/2025',
        'source_license': 'ODbL-1.0', 'league_id': EXPECTED_LEAGUE_ID,
        'source_rows': len(records), 'valid_scored_candidate_rows': n,
        'zero_zero_candidates': score_dist['0-0'],
        'unique_scored_fixture_keys': len(accepted_keys), 'unfinished_rows': unfinished,
        'quarantined_rows': len(quarantined), 'quarantine_reasons': dict(reasons),
        'quarantine_examples': quarantined[:20],
        'reference_expected_score_rows': EXPECTED_SCORED_MATCHES,
        'has_reference_coverage': n == EXPECTED_SCORED_MATCHES,
        'qa_status': 'REQUIRES_INDEPENDENT_SCORE_CHECK_AND_LICENSE_SEPARATION',
        'trainable_rows_admitted': 0, 'merged_into_2393': False,
        'production_M4_untouched': True,
        'data_provenance': 'Data from OpenLigaDB (www.openligadb.de), licensed under ODbL 1.0.',
        'notes': [
            'Reference count of 228 is a completeness check, not evidence of correctness.',
            'All scored records remain candidates until independent date, identity and score checks.',
            'Never substitute half-time, extra-time, or penalty scores for FT.',
            'Missing final scores and unplayed fixtures are not 0-0.',
            'Keep ODbL data distinct from CC0; respect attribution and share-alike.'
        ]
    }


def self_test() -> None:
    def item(i: int, day='2026-01-18T15:30:00Z', finished=True, results=None):
        return {'matchID': i, 'leagueId': 4902, 'matchDateTimeUTC': day,
                'team1': {'teamId': 1}, 'team2': {'teamId': i + 10},
                'matchIsFinished': finished, 'matchResults': results if results is not None else []}
    ht = {'resultTypeID': 1, 'resultName': 'Halbzeit', 'pointsTeam1': 2, 'pointsTeam2': 1}
    ft = {'resultTypeID': 2, 'resultName': 'Endergebnis', 'pointsTeam1': 0, 'pointsTeam2': 0}
    assert _final_result(item(1, results=[ft, ht])) == (0, 0)
    assert _final_result(item(1, results=[ht])) is None
    assert _final_result(item(1, results=[ft, ft])) is None
    assert _local_day(item(1, day='2026-07-31T16:00:00Z')) > MAX_DATE
    f = analyze([item(1, results=[ft, ht]), item(2, results=[ht]),
                 item(3, day='2026-07-31T16:00:00Z', results=[ft]),
                 item(4, finished=False), item(1, results=[ft])])
    assert f['valid_scored_candidate_rows'] == 1, f
    assert f['zero_zero_candidates'] == 1, f
    assert f['quarantined_rows'] == 3, f
    assert f['unfinished_rows'] == 1, f
    assert f['trainable_rows_admitted'] == 0, f
    print('SELFTEST PASS: full-time, 0-0, duplicates, outside-season, unfinished, fail-closed')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('json_export', nargs='?', help='Local JSON file; no automated API fetch')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--report', help='Write summary report JSON (no raw match copying)')
    ns = ap.parse_args()
    if ns.self_test:
        self_test()
    elif not ns.json_export:
        ap.error('Supply an exported JSON file or use --self-test')
    else:
        raw = json.loads(Path(ns.json_export).read_text(encoding='utf-8'))
        report = analyze(raw)
        serial = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if ns.report:
            Path(ns.report).write_text(serial, encoding='utf-8')
        print(serial)
