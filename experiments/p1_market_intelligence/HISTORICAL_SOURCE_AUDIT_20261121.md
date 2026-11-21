# P1 tarihsel fiyat veri kaynagi / ilk sonuc kontrolu — 2026-11-21

**Branch:** `experiment/p1-market-intelligence-20261121`. **Scope:** research only. Main, M4/C3, 2.6.3 v4, first/second user PDFs, historical forecast SHA and active decision index are untouched.

## Source discovery (public documentation, not acquisition)

| Source | Markets | Years/coverage | Rights and independent verification | Decision |
| --- | --- | --- | --- | --- |
| football-data.co.uk/downloadm.php | 1X2, O/U 2.5 known; BTTS coverage NOT established from inspected files | Season CSVs available 2024/25, 2025/26, 2026/27 for multiple 10-league competitions | Personal/academic research via manual or light automated (max two downloads/week); no commercial or AI-training bulk projects. Opening and closing columns documented, but fixture-level timestamp must be checked | Research candidate only; NO unauthorized bulk download |
| iddaaorananalizi.com/veri | 1X2, O/U, BTTS described | Opening/closing history claimed | Data terms explicitly prohibit scraping/bulk download or relicensing third-party raw odds. Site shows some future dates relative to 2026-11-21, so do NOT rely on advertised totals as verified today's counts | Research discovery only; NO extraction |
| footiqo.com/premium/historical-football-odds | 1X2, O/U, BTTS with market/time fields, variable coverage | 8 competitions, seasons from 2015/16 vary by league | Licensed private research/backtesting permitted; bulk website scraping prohibited; files are paid. A free 50-match sample is offered on request | Potential lawful data supply; none purchased |
| xgabora/Club-Football-Match-Data | Bet365 1X2 only documented; no confirmed O/U and BTTS prices | Broad historical leagues | Author repository advertises MIT but underlying source references football-data.co.uk; not a validated 7-event input | Insufficient 7-event source |
| tipsaudit/track-record-public | 1X2 only; no complete other 2 markets | Timestamped snapshots and settled data | CC-BY-4.0 | Partial reference only, not P1 full input |

**Original public terms:** 
- https://football-data.co.uk/contact.php
- https://football-data.co.uk/downloadm.php
- https://iddaaorananalizi.com/veri-kullanim-kosullari
- https://footiqo.com/premium/historical-football-odds/
- https://github.com/xgabora/Club-Football-Match-Data
- https://github.com/tipsaudit/track-record-public

**No new historical season rows imported as of this audit.** Do not assert 2024–2026 historical backtest is complete, or claim rights granted. Never substitute a non-iddaa quote in the live iddaa PDF path. External bookmaker archive would be a *research-only* separate-price-baseline and never represented as iddaa.

## Existing user-provided prematch snapshot records — micro outcome diagnostic

The source branch already held 12 Nov 21 archive files, of which seven contained all seven *first-PDF* price fields; five were missing O/U. Their first-PDF SHA references are in the archive but underlying raw PDF bytes and independent preco archival timestamp were not reverified. Scores were compared only after the matches were settled, **not a blind or independently timed historical evaluation**.

Scores: City–Fulham 1–1; Millwall–QPR 0–1; Norwich–Cardiff 2–1; Southampton–Derby 2–0; Alaves–Deportivo 3–1; Amed–Rizespor 0–2; Galatasaray–Samsunspor 2–1.
Result sources:
- https://www.soccerbase.com/matches/results.sd?date=2026-11-21
- https://www.tff.org/Default.aspx?pageId=198
- https://www.skysports.com/football/live-blog/13607947/manchester-city-vs-fulham-live-premier-league-match-updates-news-and-score

Seven-match **exploratory** macro average (3 market groups equally weighted; multi-class MS Brier unscaled):
- P0 Brier: **0.5309**; P1 Brier: **0.5269**.
- P0 log-loss: **0.7792**; P1 log-loss: **0.7730**.
- Difference P1–P0 Brier: **-0.0040**, far too tiny and underpowered to establish improvement.
- P0 and P1 earlier chose the same top event in all seven; no tested profit or live edge.

## Acceptance specification for a larger historical experiment

1. Separate independent source cohort for each bookmaker + price phase; source, rights, quote snapshot time and match identity. Opening and closing prices never mixed within a match.
2. Only complete 1X2, O/U 2.5 and BTTS opposite quotes for *full* 7-event P1; incomplete groups explicitly excluded or tracked as a different partial experiment, never imputed.
3. Accept fixture date/league/team resolution only with unambiguous identities. Reject repeated fixture and in-play quote; preserve source reference/rights in local manifest and quote-file SHA.
4. A publisher's opening/closing classification without fixture-specific as-of timestamp is **not** independent verification; record separate evidence grade. Timestamped files are also source assertions, not automatically authenticated.
5. Never leak final scores into fitting/selection. Holdout by kickoff date, and log score only when all prediction calculations are frozen. Run Brier (3 market families), log loss, calibration by league and season, paired bootstrap intervals. Compare P0/P1 against M4/C3 only on matching rows/time and with original historical frozen probabilities.
6. Raw user PDFs and licensed/purchased odds archives do not belong on public GitHub. Save only code, provenance summaries, aggregate test metrics and non-sensitive diagnostics.

**State:** Source research completed; historical multi-season seven-market corpus **not acquired**; no blind test or production promotion.

## 2026-11-21 owner-uploaded original PDF recovery (later supplement)

After the first source rights audit, the user's previous-conversation **original** iddaa.com PDF uploads were recovered from their own Library and parsed locally with the fixed fourteen-slot mapping. **Seven PDFs were inspected; 36 distinct, complete, non-truncated seven-quote fixtures** were admitted for purely descriptive P0/P1 replay: ENG1=4, ENG2=10, GER1=4, ESP1=3, ITA1=3, FRA1=5, NED1=3, TUR1=3, BEL1=1; POR1=0. Match dates 2026-11-20 (2) and 2026-11-21 (34). The original PDFs remain in the private conversation working folder; neither PDFs nor original seven-price vectors are committed here.

The independent research replay inverted all 36 quotes. P0 and P1 agree on the top event on **34/36**, disagree on Aston Villa–Sunderland (P0 BTTS YES / P1 MS1) and Utrecht–SC Cambuur (P0 BTTS YES / P1 OVER 2.5). Mean maximum three-family residual 1.12 percentage points, largest 2.43. Differences in event selection/fit are not demonstrated prediction skill; the 36 are not a settled matched, independently timestamp-certified blind outcomes evaluation.

Method notes: PDF embedded creation times were checked as before kickoff using Europe/Istanbul; such metadata is source evidence, NOT independent trusted timestamp proof. The oldest qualifying complete quote for a fixture is kept; later PDFs never back-change earlier price records. Truncated names or incomplete/shifted price slot rows excluded. The old German five missing O/U prices from the separate commentary archive remain incomplete; this new corpus does not retrospectively rewrite those records. The earlier seven-game micro results came from different archived first-PDF transcriptions and MUST NOT be added to 36 as an independent 43-game cohort.

**Research artifact available separately to the user:** `P1_Tarihsel_Kaynak_Arastirmasi_20261121.zip`, containing private-local replay scripts, auditable per-fixture P0/P1 derived diagnostics, league counts and original-PDF SHA reference. The package does not distribute raw user PDFs. This audit does not change production files, SHA seals, v4, or GitHub 2.6.3 live workflows. Broad 2024/25–2026/27 season odds collection and legal rights remain unresolved.
