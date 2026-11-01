"""2.6.3 offline-only integrated mathematics / quality / 17-section reporting.

This does not select fixtures, prove model quality, make real-match predictions,
retrieve odds or lineups, or change production code. All cases are explicitly
marked HYPOTHETICAL_OFFLINE_AUDIT. No market can be recommended.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from analysis_math_core import build_analysis, load_history
from data_context_263 import build_data_context
from identity_provenance_263 import audit_registry_linkage, load_registry, IdentityProvenanceError
from quality_gate_263 import (
    HISTORICAL_SHA256, QualityGateError, build_quality_report,
    locked_evidence, render_markdown,
)

VERSION = '263_integrated_offline_audit_v1'
MAX_CASES = 20

# These are completed *steps in this offline chain*, not 2.6.3 full compliance.
SECTIONS = (
    ('Ana görev ve öncelik', 'KISMI', 'Hesaplanan olasılık var; en güvenilir seçim ve sonuçlar onaylanmadı'),
    ('Güncel veri ve kaynak protokolü', 'KISMI', 'Sabit CSV denetlendi; canlı kaynak güncelliği doğrulanmadı'),
    ('Maç önü veri bütünlüğü', 'BEKLIYOR', 'Resmî fikstür, saat, ilk 11 ve oran doğrulaması yok'),
    ('Takım formu, rakip kalitesi ve veri kalitesi', 'KISMI', 'C3 rakip gücü ayrı deney; güncel form kanıtı eksik'),
    ('Kadro, taktik, psikoloji ve koşullar', 'BEKLIYOR', 'Resmî kadro/sakatlık/taktik kontrolü yok'),
    ('İstatistiksel model ve olasılıklar', 'KISMI', 'C2 k5/w0.5 ve ayrı C3 matematiksel hesap; bağımsız onay yok'),
    ('Elo takım gücü kontrolü', 'AYRI_TUTULDU', 'Önceki Elo katkısı güçlü olmadığı için otomatik etki yok'),
    ('Maç sonucu 1-X-2', 'KISMI', 'Ortak skor matrisinden çıkan fakat kalibre edilmemiş yüzdeler'),
    ('Gol pazarları', 'KISMI', 'Toplam gol ve KG ortak matristen; model terfisi yok'),
    ('İlk yarı ve doğru skor', 'KISMI', 'İlk yarı MS sinyal; çizgilerde takım modelinin üstünlüğü yok'),
    ('Korner pazarı', 'KISMI', 'Yalnız lig frekansı referansı; takım modeli terfi etmedi'),
    ('En olası tercihler', 'BEKLIYOR', 'Yüksek yüzde güvenli seçim değildir; otomatik seçim kapalı'),
    ('Matematiksel değerli seçimler', 'SONRA', 'Oran ve EV bu aşamanın dışında'),
    ('Güven, risk ve belirsizlik', 'KISMI', 'Kanıt etiketleri ve karantina; bağımsız ileri kalibrasyon yok'),
    ('Sonuç sunumu', 'KISMI', 'Offline tek/çoklu rapor var; resmî 2.6.3 canlı çıktı tamamlanmadı'),
    ('Maç önü kayıt ve maç sonu değerlendirme', 'SONRA', 'Kullanıcının isteğiyle beklemede'),
    ('25 maçlık pilot test', 'SONRA', 'Başlatılmadı'),
)


class IntegratedReportError(ValueError):
    pass


def _check_cases(cases: list[dict]) -> list[dict]:
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise IntegratedReportError('Expect 1..20 named hypothetical cases')
    keys = ('league', 'season', 'previous_season', 'target_date', 'home_id', 'away_id')
    seen = set()
    cleaned = []
    for c in cases:
        if not isinstance(c, dict) or set(c) != set(keys):
            raise IntegratedReportError('Unexpected/missing case field; no live fixture input')
        if not all(isinstance(c[k], str) and c[k].strip() and len(c[k]) <= 100 for k in keys):
            raise IntegratedReportError('Malformed case identity')
        try:
            if date.fromisoformat(c['target_date']).isoformat() != c['target_date']:
                raise ValueError('noncanonical date')
        except ValueError as ex:
            raise IntegratedReportError('Invalid target date') from ex
        if c['home_id'] == c['away_id'] or c['season'] == c['previous_season']:
            raise IntegratedReportError('Identical team or season')
        identity = (c['league'], c['target_date'], c['home_id'], c['away_id'])
        if identity in seen:
            raise IntegratedReportError('Duplicate case')
        seen.add(identity)
        cleaned.append(dict(c))
    return cleaned


def _check_records(rows: list[dict], c: dict) -> None:
    relevant = [r for r in rows if r['league'] == c['league'] and
                r['match_date'] < c['target_date'] and
                r['season'] in (c['season'], c['previous_season'])]
    teams = {t for r in relevant for t in (r['home_id'], r['away_id'])}
    if not ({c['home_id'], c['away_id']} <= teams):
        raise IntegratedReportError('Unknown team in historical source as of cutoff')
    if not any(r['season'] == c['season'] for r in relevant):
        raise IntegratedReportError('No current-season data before cutoff')
    if not any(r['season'] == c['previous_season'] for r in relevant):
        raise IntegratedReportError('No previous-season data before cutoff')


def build_offline_bundle(rows: list[dict], source: dict, evidence: dict,
                         cases: list[dict], require_locked_source: bool = True,
                         identity_audit: dict | None = None) -> dict:
    """Build entire pipeline in-memory: no third-party supplied probabilities accepted.

    Set require_locked_source=False only in synthetic *unit tests*.
    """
    cases = _check_cases(cases)
    if require_locked_source and source.get('sha256') != HISTORICAL_SHA256:
        raise IntegratedReportError('Historical data snapshot SHA-256 mismatch; fail closed')
    if source.get('rows') != len(rows):
        raise IntegratedReportError('History count/provenance mismatch')
    if evidence.get('coverage', {}).get('target_matches') != 880:
        raise IntegratedReportError('Acceptance provenance failed')
    # Offline identity evidence is optional for legacy synthetic tests, but when
    # supplied it MUST be complete and bound to the exact same history digest.
    # No caller-controlled Boolean can be used to elevate model reliability.
    if identity_audit is not None and (
        not isinstance(identity_audit, dict) or
        identity_audit.get('status') != 'OFFLINE_REGISTRY_LINKAGE_VALIDATED' or
        identity_audit.get('history_sha256') != source.get('sha256') or
        identity_audit.get('historical_rows_linked') != len(rows) or
        identity_audit.get('independently_verified_official_fixture') is not False or
        identity_audit.get('independently_verified_squad_or_lineups') is not False
    ):
        raise IntegratedReportError('Historical identity attestation did not match locked data')
    results = []
    for c in cases:
        _check_records(rows, c)
        analysis = build_analysis(rows, source, league=c['league'], season=c['season'],
                                  previous_season=c['previous_season'], target_date=c['target_date'],
                                  home=c['home_id'], away=c['away_id'])
        quality = build_quality_report(analysis, rows, source, evidence)
        data_context = build_data_context(rows, source, c)
        data_context['registry_linkage'] = {
            'status': 'NOT_CHECKED' if identity_audit is None else identity_audit['status'],
            'registry_sha256': None if identity_audit is None else identity_audit['registry_sha256'],
            'historical_rows_linked': None if identity_audit is None else identity_audit['historical_rows_linked'],
            'does_not_verify_live_fixture_or_lineup': True,
        }
        if quality['recommendations'] or quality['best_pick'] is not None or quality['high_probability_alert'] is not None:
            raise IntegratedReportError('Unsafe recommendations appeared in offline result')
        all_markets = quality['markets'] + quality['experimental_audit']
        if any(m.get('can_recommend') is not False or m.get('calibrated') is not False
               for m in all_markets):
            raise IntegratedReportError('Unapproved market was marked approved')
        results.append({'identity': c, 'analysis': analysis, 'quality': quality, 'data_context': data_context})
    return {'version': VERSION, 'scope': 'HYPOTHETICAL_OFFLINE_AUDIT',
            'not_live_match_analysis': True, 'production_changed': False,
            'real_fixture_verified': False, 'odds_EV': None,
            'model_promotions': [], 'recommendations': [],
            'data_provenance': source,
            'acceptance_sha256': evidence.get('source', {}).get('sha256'),
            'historical_identity_linkage': {
                'status': 'NOT_CHECKED' if identity_audit is None else identity_audit['status'],
                'registry_sha256': None if identity_audit is None else identity_audit['registry_sha256'],
            },
            'sections': [{'number': i, 'title': name, 'status': status, 'reason': reason}
                         for i, (name, status, reason) in enumerate(SECTIONS, 1)],
            'cases': results}


def _safe(s: object) -> str:
    return re.sub(r'[|\r\n]', ' ', str(s)).replace('`', "'")


def render_bundle_markdown(bundle: dict) -> str:
    if bundle.get('scope') != 'HYPOTHETICAL_OFFLINE_AUDIT' or not bundle.get('not_live_match_analysis'):
        raise IntegratedReportError('Not an offline report')
    lines = ['# 2.6.3 — Birleşik offline analiz ve dürüstlük raporu', '',
             '**GERÇEK MAÇ TAHMİNİ DEĞİLDİR.** Fikstür doğrulaması, ilk 11, oran/EV, öneri, pilot ve sonuç kaydı yapılmadı.',
             'Önceden incelenmiş 2026/27 sonuçları yalnız tarihsel deney kanıtıdır; bağımsız ileri başarı kanıtı değildir.',
             '', '## 17 bölüm uygunluk durumu', '',
             '| Bölüm | Durum | Neden |', '|---|---|---|']
    for s in bundle['sections']:
        lines.append(f"| {s['number']}. {_safe(s['title'])} | {_safe(s['status'])} | {_safe(s['reason'])} |")
    lines.extend(['', '## Vaka sonuçları — yalnız varsayımsal/offline', ''])
    for i, case in enumerate(bundle['cases'], 1):
        identity = case['identity']
        quality = case['quality']
        context = case['data_context']
        lines.append(f"### {i}. {_safe(identity['league'])}: {_safe(identity['home_id'])} – {_safe(identity['away_id'])}")
        lines.append(f"Veri kesimi (gün hariç): **{_safe(identity['target_date'])}**. Kaynak SHA-256: `{_safe(quality['provenance']['sha256'])}`.")
        lines.append('')
        lines.append('| Model | Durum |')
        lines.append('|---|---|')
        for model, status in quality['model_coverage'].items():
            lines.append(f'| {_safe(model)} | {_safe(status)} |')
        lines.extend(['', '#### Pazar kalite dökümü', ''])
        # Delegate single source of truth for market reliability to the quality gate.
        quality_markdown = render_markdown(quality)
        start = quality_markdown.index('| Pazar |')
        end = quality_markdown.index('## Deneysel alternatif', start)
        lines.append(quality_markdown[start:end].strip())
        lines.extend(['', '#### C3 deneysel alternatif',
                      'C3 ana modelin otomatik yerine geçmez.'])
        for row in quality['experimental_audit'][:6]:
            val = '—' if row['probability'] is None else f"{100*row['probability']:.1f}%"
            lines.append(f"- {_safe(row['market'])}: {val} — {_safe(row['status'])}; önerilebilir: HAYIR")
        lines.extend(['', '#### Kaynak, örneklem ve güncellik dürüstlüğü', ''])
        id_status = context['registry_linkage']
        lines.append('Tarihsel takım/fikstür kimliği: **' + _safe(id_status['status']) + '**; GitHub Actions kayıt dosyası gerçek zamanlı resmî kaynak doğrulaması değildir.')
        if id_status['registry_sha256']:
            lines.append('Sabit kimlik kayıt özeti SHA-256: `' + _safe(id_status['registry_sha256']) + '`.')
        counts = context['eligible_league_games']
        lines.append(f"Lig veri kapsamı (kesim öncesi): güncel sezon **{counts['current_season']}**, önceki sezon **{counts['previous_season']}** maç.")
        for team in ('home', 'away'):
            t = context['team_context'][team]
            context_n = t['current_home'] if team == 'home' else t['current_away']
            lines.append(f"- {('Ev' if team == 'home' else 'Deplasman')} takımının ilgili saha örneklemi: **{context_n}** maç.")
        dates = context['last_historical_result_dates']
        lines.append(f"Son gözlenen lig maç tarihi: **{_safe(dates['last_league_result'] or 'YOK')}**. Bu tarih, aradaki bütün maçların kaydedildiğinin kanıtı değildir.")
        providers = context['provenance']['historical_source_references']
        lines.append(f"CSV kaynak referansları: {_safe(', '.join(sorted(providers)) if providers else 'YOK')}; URL'ler bağımsız erişim/doğrulama kanıtı değildir.")
        cov = context['current_season_market_coverage']
        for field, label in [('final_goals','Gol'),('first_half','İlk yarı'),('full_time_corners','Korner'),('shots','Şut'),('xg','CSV içi xG')]:
            lines.append(f"- {label}: **{cov[field]['usable']}/{cov[field]['total']}** kullanılabilir maç.")
        lines.append('Resmî fikstür, ilk 11, sakatlık/ceza ve taktik kaynakları: **HENÜZ KONTROL EDİLMEDİ**. İnternet üzerinden doğrulama yapılmadı.')
        if context['review_flags']:
            lines.append('Kontrol bekleyen alanlar: ' + _safe(', '.join(context['review_flags'])))
        lines.extend(['', '#### Dış bilgi ve ertelenen alanlar',
                      'Resmî fikstür/ilk 11, güncel taktik/kadro, xG, Elo, oran/EV ve sonuç takibi doğrulanmadı.',
                      'Hesaplanan oranlar model çıktısıdır, kalibrasyon veya bahis tavsiyesi değildir.', ''])
    lines.extend(['## Genel kabul kararı', '',
                  '**TAM UYUM YOK.** Matematik/kalite zinciri offline olarak bağlandı; tüm pazarlar öneriye kapalı.',
                  'Sıradaki çalışma: gerçek veri kaynağı ve 2.6.3 analiz bağlamındaki eksikleri birleştirmek; pilot/gerçek maç kayıtları sonra.', ''])
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description='Only offline hypothetical match audit; no live predictions')
    p.add_argument('--history', required=True)
    p.add_argument('--evidence', required=True)
    p.add_argument('--registry', help='Historical registry JSON extracted from the SAME frozen source artifact')
    p.add_argument('--registry-sha256', help='Expected registry SHA-256; mandatory with --registry')
    p.add_argument('--cases', required=True, help='JSON list of abstract explicit cases, max 20')
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-markdown', required=True)
    a = p.parse_args()
    rows, source = load_history(a.history)
    evidence = locked_evidence(a.evidence)
    cases = json.loads(Path(a.cases).read_text(encoding='utf-8'))
    if bool(a.registry) != bool(a.registry_sha256):
        raise IntegratedReportError('--registry and --registry-sha256 must be provided together')
    identity_audit = None
    if a.registry:
        registry, sha = load_registry(a.registry, expected_sha256=a.registry_sha256)
        identity_audit = audit_registry_linkage(rows, source, registry, sha)
    bundle = build_offline_bundle(rows, source, evidence, cases, identity_audit=identity_audit)
    # Defensive: no overwrite by default for audit artifacts, no append-only forecast ledger created.
    for target in (a.out_json, a.out_markdown):
        if Path(target).exists():
            raise IntegratedReportError('Refuse overwriting existing audit output')
    Path(a.out_json).write_text(json.dumps(bundle, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    Path(a.out_markdown).write_text(render_bundle_markdown(bundle), encoding='utf-8')
    print(json.dumps({'status': bundle['scope'], 'cases': len(bundle['cases']),
                      'recommendations': 0, 'production_changed': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
