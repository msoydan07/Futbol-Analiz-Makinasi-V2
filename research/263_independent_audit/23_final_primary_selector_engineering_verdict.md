# 2.6.3 — Final independent engineering choice: one event per match

**Date:** 20 November 2026. **Version:** C3-2025-frozen-binary-calibration shadow v1. **Status:** implemented and independently exercised on original historical cohorts and 39 real SHA matches. **Not silently promoted to live engine.**

## Goal and actual code

We keep M4's **existing frozen August 2026 joint MS** distribution. Only KG and 2.5 goals use a C3 binary calibration, learned once from **2,898 C3-supported as-of games during 2025/26**, with two separate L2 logistic models and the previous-day league base as the second input. No xG, no bookmaker prices, and no new manual input are required.

Each of MS1, MSX, MS2, KG Yes, KG No, Over 2.5 and Under 2.5 is a candidate. After coherent family normalization, the **highest calibrated probability** becomes the sole main preference. The strongest alternative from another family is included. If the top two probabilities differ by no more than two percentage points, the choice is flagged **NEAR TIE / LIMITED DISCRIMINATION**; that is NOT an arbitrary automatic PAS. Missing C3 is explicitly flagged as uncalibrated M4 fallback if valid, otherwise an honest PAS.

We have created a ready-to-call **pure Python shadow production-shaped module**:
- `research/263_independent_audit/shadow_primary_choice_final.py`
- Signed-via-Git policy content `research/263_independent_audit/20_shadow_choice_policy.json`
- A separate, source-faithful and deterministic full-replay test `research/263_independent_audit/audit_frozen_shadow_validation.py`

For KG Var, `q = sigmoid(0.120946 + 0.2643173*logit(C3_KG_Var) + 0.5012377*logit(asof_league_KG_Var))`. For 2.5 Üst, `q = sigmoid(0.1100003 + 0.2639998*logit(C3_O25) + 0.2514675*logit(asof_league_O25))`. The opposite two outcomes are exactly `1-q`.

## Comparison (same match, exactly one main decision)

| Cohort | N | Old main hit | New main hit | Old mean confidence | New mean confidence | Old choice Brier | New choice Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026/27 Aug–Oct retrospectively reconstructed raw M4 MS | 873 | 57.617% | **62.543%** | 62.046% | 59.721% | 0.239537 | **0.231507** |
| 2026 Sep–Oct, valid frozen August joint MS (more live-like) | 615 | 56.423% | **59.512%** | 62.480% | 60.129% | 0.243082 | **0.237011** |
| Nov 8 originals, true pre-kickoff SHA, one date | 39 | **69.231%** | **69.231%** | 63.227% | 60.834% | **0.203286** | 0.205372 |

Across 873 raw MS-era matches the nominal day-block bootstrap hit improvement is **+4.9255 percentage points, 95% CI [+1.418, +8.873]**. This is not an independent blind inference after many candidate methods were inspected. In the **more operation-matching 615 frozen-MS cohort**, hit gain **+3.0894 points with CI [-0.621, +7.131]**, crossing zero. The 39 original SHA are just **one calendar day**, showing equal hit rate, not independent proof of superiority.

The previous 2025/26 M4 tuning and earlier studies of 2026/27 outcomes render all of these comparative studies **exploratory**, although predictions use chronological previous-date inputs only.

## Implementation confidence

The frozen 7-decimal coefficients were compared against original independent sklearn fitting on 2025 C3 cases: **exactly zero main-choice mismatches** across 873 raw-M4, 615 correctly calibrated M4-MS and 39 authentic SHA matches. Maximum raw probability difference was approximately **1.7e-8**. The strict API was also exercised with real original forecast-created/kickoff timestamps on all **39** actual SHA records, and blocked post-kickoff calls, naive timestamps, invalid probability family sums and missing forecasts. Same-day score labels are not part of the selection function.

**CI success:**
- Comparison with alternative calibration candidates: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44816364551
- Source-immutable coefficient/API/matchday contract verification: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44817133988

## Engineer's decision

I select **M4 frozen August MS + C3 2025-trained binary logistic calibration + one highest-calibrated-probability main pick** as the **best current research candidate**, because it ranks strongly across different already-reviewed retrospective cohorts, preserves MS and avoids assuming KG/O25 raw probabilities have the same reliability. The method is concretely written, pinned, tested and runnable in a separate branch. **It is not guaranteed to outperform on future games**; given prior repeated research and one day of true SHA, the correct lifecycle state is shadow-only until independent chronological live evidence across more dates is available. This is not a request to launch another manually curated pilot: the existing scheduled seal/result observation process already exists, but it has not been automatically rewired.

**Protected:** Main 2.6.3 code, original score and SHA archives, 10 leagues, existing automations and PDF generation unchanged. 4,413 source SHA = `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.

## Reproducible assets

- [Full eight-candidate statistics and same-day-block uncertainty](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/18_candidate_selector_result.json)
- [Frozen-model faithful replay and SHA-clock verification](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/21_frozen_shadow_validation.json)
- [Frozen, usable single-event selector](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/shadow_primary_choice_final.py)
- [Frozen parameters](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/20_shadow_choice_policy.json)
