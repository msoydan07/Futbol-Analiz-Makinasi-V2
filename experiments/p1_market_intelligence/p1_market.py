"""P1: independent read-only market intelligence research; no core 2.6.3 imports.

P0 = margin-free 1X2, 2.5 and BTTS probabilities. P1 = independent
Poisson score surface fit to all three P0 market families, using morning odds
ONLY. It is a *re-expression* of prices, not new information or a proven edge.

Python 3.11, standard library only. This module never modifies sealed forecasts.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MARKETS = {
    'MS': ('MS1', 'MSX', 'MS2'),
    'OU25': ('UNDER_2.5', 'OVER_2.5'),
    'KG': ('BTTS_YES', 'BTTS_NO'),
}
P1_VERSION = 'P1_INDEPENDENT_POISSON_MARKET_INVERSION_V1'
ALL_CHOICES = tuple(k for ks in MARKETS.values() for k in ks)

class MarketDataError(ValueError):
    pass


def _sha_json(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _timestamp(s: str) -> datetime:
    try:
        t = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        if t.tzinfo is None:
            raise ValueError('timezone required')
        return t
    except (ValueError, TypeError) as e:
        raise MarketDataError('TIMESTAMP_INVALID') from e


def no_vig(prices: dict[str, float], method: str = 'proportional') -> dict:
    """One mutually exclusive *complete* market only; never normalize 7 jointly."""
    if not isinstance(prices, dict) or not prices:
        raise MarketDataError('EMPTY_MARKET')
    odds = []
    for k, v in prices.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not (1.0 < v <= 1000.0):
            raise MarketDataError('INVALID_ODDS:' + str(k))
        odds.append(float(v))
    q = [1.0 / x for x in odds]
    s = sum(q)
    if s <= 0:
        raise MarketDataError('INVALID_OVERROUND')
    if method == 'proportional':
        p = [x / s for x in q]
    elif method == 'additive':
        p = [x - (s - 1.0) / len(q) for x in q]
        if min(p) <= 0:
            raise MarketDataError('ADDITIVE_NEGATIVE_PROBABILITY')
    elif method == 'power':
        lo, hi = 0.0001, 100.0
        for _ in range(100):
            mid = (lo + hi) / 2.0
            if sum(x ** mid for x in q) > 1.0:
                lo = mid
            else:
                hi = mid
        p = [x ** ((lo + hi) / 2.0) for x in q]
    else:
        raise MarketDataError('UNKNOWN_NO_VIG_METHOD')
    p = [x / sum(p) for x in p]
    return {'method': method, 'probabilities': dict(zip(prices, p)),
            'book_margin': s - 1.0}


def _poisson_probs(lam: float, size: int = 28) -> list[float]:
    if not 0.05 <= lam <= 5.5:
        raise MarketDataError('GOAL_EXPECTATION_OUTSIDE_BOUNDS')
    arr = [math.exp(-lam)]
    for k in range(1, size + 1):
        arr.append(arr[-1] * lam / k)
    return arr


def poisson_markets(home: float, away: float) -> dict[str, dict[str, float]]:
    ph, pa = _poisson_probs(home), _poisson_probs(away)
    ca = 0.0
    homewin, draw = 0.0, 0.0
    for i, h in enumerate(ph):
        homewin += h * ca
        draw += h * pa[i]
        ca += pa[i]
    awaywin = 1.0 - homewin - draw
    if min(homewin, draw, awaywin) < -1e-9:
        raise MarketDataError('POISSON_NUMERICAL_ERROR')
    total = home + away
    under = math.exp(-total) * (1.0 + total + (total ** 2) / 2.0)
    yes = (1.0 - math.exp(-home)) * (1.0 - math.exp(-away))
    return {'MS': {'MS1': homewin, 'MSX': draw, 'MS2': max(0.0, awaywin)},
            'OU25': {'UNDER_2.5': under, 'OVER_2.5': 1.0 - under},
            'KG': {'BTTS_YES': yes, 'BTTS_NO': 1.0 - yes}}


def _fit_loss(h: float, a: float, reference: dict) -> float:
    predicted = poisson_markets(h, a)
    # Average proper KL discrepancy across the three distinct market families.
    return sum(sum(p * math.log(p / max(predicted[g][k], 1e-15))
                   for k, p in reference[g].items() if p > 0)
               for g in MARKETS) / 3.0


def _golden_min(fn, lo: float, hi: float) -> float:
    tau = (math.sqrt(5) - 1.0) / 2.0
    c, d = hi - tau * (hi - lo), lo + tau * (hi - lo)
    fc, fd = fn(c), fn(d)
    for _ in range(44):
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - tau * (hi - lo)
            fc = fn(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + tau * (hi - lo)
            fd = fn(d)
    return (lo + hi) / 2.0


def fit_inverse_poisson(reference: dict) -> dict:
    if set(reference) != set(MARKETS) or any(set(reference[g]) != set(MARKETS[g]) for g in MARKETS):
        raise MarketDataError('ALL_THREE_COMPLETE_MARKET_GROUPS_REQUIRED')
    for g in MARKETS:
        p = reference[g]
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v < 1 for v in p.values()) or abs(sum(p.values()) - 1) > 1e-7:
            raise MarketDataError('INVALID_PROBABILITY_VECTOR:' + g)
    starts = (0.4, 0.75, 1.15, 1.7, 2.5, 3.5, 4.8)
    seeds = sorted(((_fit_loss(h, a, reference), h, a) for h in starts for a in starts))[:5]
    best = (float('inf'), None, None)
    for _, h, a in seeds:
        for _ in range(11):
            old_h, old_a = h, a
            h = _golden_min(lambda x: _fit_loss(x, a, reference), 0.05, 5.5)
            a = _golden_min(lambda x: _fit_loss(h, x, reference), 0.05, 5.5)
            if abs(h - old_h) + abs(a - old_a) < 1e-9:
                break
        loss = _fit_loss(h, a, reference)
        if loss < best[0]:
            best = (loss, h, a)
    loss, h, a = best
    predicted = poisson_markets(h, a)
    residuals = {g: {k: 100 * (predicted[g][k] - reference[g][k])
                     for k in MARKETS[g]} for g in MARKETS}
    max_gap = max(abs(v) for d in residuals.values() for v in d.values())
    return {'lambda_home': h, 'lambda_away': a,
            'kl_mismatch': loss,
            'p1_probabilities': predicted,
            'residual_points': residuals,
            'max_residual_pp': max_gap,
            'coherence_warning': 'MARKET_FIT_CONFLICT' if max_gap > 8.0 else 'NONE',
            'algorithm': P1_VERSION}


def best_choices(probabilities: dict) -> dict:
    candidates = [(probabilities[g][k], g, k) for g in MARKETS for k in MARKETS[g]]
    candidates.sort(key=lambda c: (-c[0], c[2]))
    main = candidates[0]
    alternate = next(c for c in candidates if c[1] != main[1])
    runner = candidates[1]
    def fmt(x): return {'choice': x[2], 'family': x[1], 'probability': x[0]}
    return {'main': fmt(main), 'alternative_different_family': fmt(alternate),
            'runner_up_overall': fmt(runner),
            'top_two_gap_pp': 100.0 * (main[0] - runner[0]),
            'top_two_close': 100.0 * (main[0] - runner[0]) <= 2.0,
            'not_profitability_or_guarantee': True}


def analyze_prices(market_prices: dict, margin_method: str = 'proportional') -> dict:
    if not isinstance(market_prices, dict) or set(market_prices) != set(MARKETS):
        raise MarketDataError('INCOMPLETE_MARKET_GROUPS')
    normalized = {}
    for g in MARKETS:
        if set(market_prices[g]) != set(MARKETS[g]):
            raise MarketDataError('INCOMPLETE_OPPOSITES:' + g)
        normalized[g] = no_vig(market_prices[g], margin_method)
    p0 = {g: normalized[g]['probabilities'] for g in MARKETS}
    p1 = fit_inverse_poisson(p0)
    other_methods = {}
    for m in ('proportional', 'additive', 'power'):
        try:
            other_methods[m] = {g: no_vig(market_prices[g], m)['probabilities'] for g in MARKETS}
        except MarketDataError as e:
            other_methods[m] = {'unavailable_reason': str(e)}
    max_method_spread = max((max(abs(other_methods[x][g][k] - other_methods[y][g][k])
                             for x in other_methods for y in other_methods
                             if g in other_methods[x] and g in other_methods[y])
                             for g in MARKETS for k in MARKETS[g]), default=0.0)
    return {'p0': p0, 'margins': {g: normalized[g]['book_margin'] for g in MARKETS},
            'margin_method': margin_method, 'method_comparison': other_methods,
            'max_margin_method_spread_pp': 100 * max_method_spread,
            'p0_select': best_choices(p0), 'p1': p1,
            'p1_select': best_choices(p1['p1_probabilities'])}


def archive_record_to_input(record: dict, name: str) -> dict:
    """Only archived FIRST prices; no second quotes or final scores used."""
    if record.get('schema') != '263_SECOND_PDF_COMMENTARY_APPEND_ONLY_V1':
        raise MarketDataError('UNRECOGNIZED_ARCHIVE_SCHEMA')
    fingerprint = record.get('record_sha256')
    if not isinstance(fingerprint, str) or fingerprint != _sha_json({k: v for k, v in record.items() if k != 'record_sha256'}):
        raise MarketDataError('ARCHIVE_RECORD_HASH_MISMATCH')
    pdfhash = record.get('source_pdf_fingerprints', {}).get('first_pdf_sha256')
    if not isinstance(pdfhash, str) or len(pdfhash) != 64 or any(c not in '0123456789abcdef' for c in pdfhash):
        raise MarketDataError('FIRST_PDF_FINGERPRINT_MISSING')
    group = record.get('second_pdf_observation', {}).get('quoted_families', {})
    def take(key: str, expected: int) -> list:
        entry = group.get(key, {})
        odds = entry.get('before') if isinstance(entry, dict) else None
        if not isinstance(odds, list) or len(odds) != expected:
            raise MarketDataError('INCOMPLETE_FIRST_PDF_GROUP:' + key)
        return odds
    ms = take('MS_1_X_2', 3)
    uo = take('OVER_UNDER_2_5', 2)
    kg = take('BTTS_YES_NO', 2)
    # This legacy archive's ambiguous OVER_UNDER_2_5 field is actually
    # [UNDER, OVER], matching iddaa_pdf_bulletin_263.py O25_UNDER,O25_OVER.
    prices = {'MS': dict(zip(MARKETS['MS'], ms)),
              'OU25': dict(zip(MARKETS['OU25'], uo)),
              'KG': dict(zip(MARKETS['KG'], kg))}
    match = record.get('match') or {}
    for k in ('home', 'away', 'league', 'date_tr'):
        if not isinstance(match.get(k), str) or not match[k]:
            raise MarketDataError('MATCH_IDENTITY_MISSING')
    return {'source_archive_path': name, 'match': match,
            'first_pdf_sha256': pdfhash,
            'archive_kind': record.get('record_kind'),
            'source_class': 'ARCHIVED_USER_PDF_TRANSCRIPTION_NOT_INDEPENDENTLY_PDF_VERIFIED',
            'prices': prices}


def run_archive(directory: Path, *, margin_method: str = 'proportional') -> dict:
    if not directory.is_dir():
        raise MarketDataError('ARCHIVE_DIR_NOT_FOUND')
    records, exclusions = [], []
    seen = set()
    for path in sorted(directory.glob('*.json')):
        if path.name == 'index.json':
            continue
        try:
            source = archive_record_to_input(json.loads(path.read_text(encoding='utf-8')), str(path))
            identity = tuple(source['match'][k] for k in ('league', 'date_tr', 'home', 'away'))
            if identity in seen:
                raise MarketDataError('DUPLICATE_MATCH')
            seen.add(identity)
            analyzed = analyze_prices(source['prices'], margin_method)
            records.append({**{k:v for k,v in source.items() if k!='prices'}, 'analysis': analyzed})
        except (MarketDataError, ValueError, KeyError, TypeError) as exc:
            exclusions.append({'file': path.name, 'reason': str(exc)})
    return {'schema': 'P1_RESEARCH_ARCHIVE_DESCRIPTIVE_V1', 'version': P1_VERSION,
            'total_archive_files': len(records) + len(exclusions),
            'full_quotes_analyzed': len(records), 'excluded': exclusions,
            'source_warning': 'Archived transcriptions; original PDF bytes not rechecked. No external bookmaker data.',
            'historical_outcome_comparison': 'NOT_RUN_NO_AUDITED_PRE_KICKOFF_PRICE_AND_RESULT_PAIRS',
            'claims_of_better_predictive_accuracy': False,
            'P1_is_price_reexpression_not_independent_signal': True,
            'records': records}


def score_observed(probs: dict, home_goals: int, away_goals: int) -> dict:
    """Scoring helper; caller must independently validate fixture, result, as-of time.

    Returns 3 proper per-market scores, not seven independent Bernoulli games.
    """
    if (isinstance(home_goals, bool) or isinstance(away_goals, bool)
            or not isinstance(home_goals, int) or not isinstance(away_goals, int)
            or min(home_goals, away_goals) < 0):
        raise MarketDataError('INVALID_FINAL_SCORE')
    truth = {'MS': 'MS1' if home_goals > away_goals else 'MS2' if home_goals < away_goals else 'MSX',
             'OU25': 'OVER_2.5' if home_goals + away_goals > 2 else 'UNDER_2.5',
             'KG': 'BTTS_YES' if min(home_goals, away_goals) > 0 else 'BTTS_NO'}
    brier, logloss = {}, {}
    for group in MARKETS:
        selected = truth[group]
        brier[group] = sum((probs[group][k] - float(k == selected)) ** 2 for k in MARKETS[group])
        logloss[group] = -math.log(max(1e-15, probs[group][selected]))
    return {'truth': truth, 'brier_by_market': brier, 'log_loss_by_market': logloss,
            'macro_brier': sum(brier.values()) / 3,
            'macro_log_loss': sum(logloss.values()) / 3}


def cli():
    parser = argparse.ArgumentParser(description='Independent P1 market inversion (read-only)')
    parser.add_argument('--archive-dir', type=Path, required=True)
    parser.add_argument('--method', choices=('proportional', 'additive', 'power'), default='proportional')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run_archive(args.archive_dir, margin_method=args.method)
    content = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content)


if __name__ == '__main__':
    cli()
