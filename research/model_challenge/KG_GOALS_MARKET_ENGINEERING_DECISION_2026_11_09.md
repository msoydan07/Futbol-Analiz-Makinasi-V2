# KG / ALT–ÜST MATEMATİK ARAŞTIRMASI — 9 Kasım 2026

## Amaç ve kaynak
M4'ün KG Var ve toplam gol çizgilerindeki olasılık kalitesini,
mevcut MS olasılıklarını bozup bozmadığını da gözleyerek ölçmek.

- Owner-approved limited-research source: **4.518 matches**, 10 leagues;
  immutable source SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`
- 2026/27 historical August–September: **587** matched matches (DEV).
- 2026/27 October–November 3: **397** matched matches (EVAL).
- 1 missing M4 prediction; never imputed.
- The evaluation period has **already been viewed in earlier research**.
  Results are strictly exploratory, not a new independent holdout.
- Week-start cutoffs prevent current-week match results from entering the
  model fit for any evaluated match. This is less current than actual
  match-morning forecasting.
- Existing M4 code/settings (360-day half life, Ridge 4/48) unchanged.

## Models tested
All four models produce a mathematically coherent joint full-time
score probability distribution, so 1X2, BTTS and OVER_1.5/2.5/3.5 are
all derived from **the same** joint distribution.
1. Original independent-Poisson M4
2. Shared multiplier on both M4 expected goal rates, dev-selected grid
   scale 0.85,0.925,1.0,1.075,1.15
3. Dixon–Coles 0-0 / 0-1 / 1-0 / 1-1 correction with
   shared lambda scale and rho -0.15,-0.075,0,0.075,0.15
4. Bivariate Poisson with shared-goal covariance c in
   0,.10,.20,.30 and same multiplier grid, preserving both
   marginal expected goals after the scale.

Selection was made using DEV only, on mean Brier of BTTS and
OVER 1.5, 2.5, 3.5, with multiclass MS Brier worsening of at most
0.003 relative to original M4. The entire candidate grid and
guardrail were authored *before the CI evaluation*.

### Parameters selected using development only
- Original M4: independent, scale 1
- Scaled M4: scale **1.15**
- Dixon–Coles: scale **1.15**, rho **0** (so it is exactly scaled M4)
- Bivariate Poisson: scale **1.15**, shared covariance **0.30**

Both the scale and covariance reached the EDGE of the predefined
grid, warning against any inference of stable optimum. We are not
extending or re-tuning the grid on the observed evaluation results.

## Equal-fixture October/November evaluation
Lower Brier is better.

| Candidate | BTTS_YES | OVER_2.5 | Mean 4 goal-market Brier | 1X2 multiclass Brier |
|---|---:|---:|---:|---:|
| Original M4 | **0.249457** | 0.250775 | 0.226355 | 0.575728 |
| Scaled lambda | 0.251894 | 0.248318 | 0.226530 | **0.573544** |
| Dixon–Coles | 0.251894 | 0.248318 | 0.226530 | **0.573544** |
| Bivariate Poisson | 0.253111 | **0.246840** | **0.226020** | 0.577791 |

Findings:
- **No broad improvement in both requested markets.** All proposed
  alternatives worsen BTTS Brier versus original M4.
- Bivariate Poisson modestly improves 2.5 O/U, worsens BTTS and 1X2.
- Improved OVER_2.5 alone is not a model-quality victory.
- Dixon–Coles selects rho=0: no data-supported dependence
  correction, at least under this grid/data/window.
- The best four-market aggregate difference is only
  -0.000335 Brier (bivariate minus M4), much smaller than a
  convincing practical promotion margin.
- A real improvement claim would require a predeclared prospectively
  sealed evaluation and uncertainty assessment. This test does not
  establish superiority, betting edge, or profitability.

## Ek kök-neden kontrolü — beklenen gollerin sapması
Aynı dondurulmuş deneyin yalnızca betimsel teşhisi:
- Ağustos–Eylül (587 maç): ortalama toplam lambda **2.8346**,
  gerçekleşen ortalama toplam gol **3.0562**.
  Ev lambdası 1.5454, gerçek 1.6593; deplasman lambdası 1.2892,
  gerçek 1.3969.
- Ekim–3 Kasım (397 maç): toplam lambda **2.9010**,
  gerçek toplam gol **3.1335**.
  Ev lambdası 1.5959, gerçek 1.7179; deplasman lambdası 1.3050,
  gerçek 1.4156.

Bu örneklerde toplam gol beklentisi gerçekleşen ortalama gollerden
yaklaşık **%7–8 düşük**. Ancak bütün lambdaları büyütmek bu
testte KG pazarını kötüleştirdi, yani tek başına çözüm değildir.
Bu betimsel fark maç bazlı kalibrasyon üstünlüğünü kanıtlamaz.

## Decision — NOT PROMOTED
**Keep existing M4 unchanged for goals and BTTS.**
Research diagnostics suggest that a model-level global goal-rate
increase may benefit total goals but can materially harm BTTS. A
single universal scaling or score-dependence parameter is unlikely
to solve both markets reliably.

Next distinct diagnostic (without modifying the incumbent):
1. Quantify systematic home/away/total lambda residuals and separately
   calibration bins for KG and each goal line, comparing to league
   as-of empirical baselines.
2. If testable: candidate *market-specific* probability calibration
   learned on one chronological period. Because independent market
   calibrations can contradict a coherent full-time score distribution,
   never silently replace a single market without a documented joint
   coherence policy.
3. Reserve new prospective SHA-sealed fixtures as the actual acceptance
   test, because October results were already viewed.

## Reproducibility
- Script: `research/model_challenge/goal_market_distribution_challenge.py`
- Invariants: `research/model_challenge/test_goal_market_distribution_challenge.py`
- Run: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42574373913
- Artifact: `goalmarket-263-poisson-dc-bivar-locked-results`
- Production 2.6.3 code, morning sealed predictions, source history unchanged.
