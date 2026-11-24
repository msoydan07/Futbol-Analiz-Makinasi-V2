#!/usr/bin/env python3
# coding: utf-8
"""Hakem 2: frozen performance-selector integration for the research daily router.

No probability blending. Research-only 504-match rule, trained on archive odds
proxies, NOT verified as real iddaa/M4 forward advantage. Never fabricates M4.
A missing/partial expert is never treated as a three-source referee decision.
"""
from __future__ import annotations
import json
from pathlib import Path
from HAKEM_KARAR_UYGULA_V1 import EVENTS, FAMILIES, NAMES, SOURCES, validate

RULE_SCHEMA = "HAKEM2_PERFORMANCE_SELECTOR_RESEARCH_V1"
SOURCE_MAP = {
    "FUTBOL_M4_C3_V4_REBUILT": "M4_C3_V4",
    "ARSIV_P0_PROXY": "P0",
    "HAFIZA_V1_2_RETRO": "HAFIZA",
}
EXPECTED_SOURCES = tuple(SOURCE_MAP)

class Hakem2Error(ValueError):
    pass

def load_h2_rule(path):
    rule = json.loads(Path(path).read_text(encoding="utf-8"))
    if (rule.get("schema") != RULE_SCHEMA or
        rule.get("status") != "RESEARCH_ONLY_NOT_LIVE_CALIBRATED" or
        rule.get("training_n") != 504 or
        rule.get("train_cutoff_exclusive") != "2026-11-01" or
        rule.get("source_order") != list(EXPECTED_SOURCES) or
        set(rule.get("chosen_by_family", {})) != set(FAMILIES) or
        rule.get("source_archive_sha256") !=
          "f80d9646af7d68249afa4445266fa7c721d64ed14b88b53579bf47a691ff13d0"):
        raise Hakem2Error("UNRECOGNIZED_OR_NOT_FROZEN_HAKEM2_RULE")
    for fam, src in rule["chosen_by_family"].items():
        if src not in SOURCE_MAP:
            raise Hakem2Error("UNKNOWN_HAKEM2_SOURCE_" + fam)
    return rule

def direct_recommendations(experts):
    out = {}
    for source, vector in experts.items():
        if source not in SOURCES or not isinstance(vector, dict):
            continue
        if set(vector) != set(EVENTS) or any(vector[k] is None for k in EVENTS):
            out[source] = {"status": "PARTIAL_PROBABILITY_NO_MAIN_CHOICE"}
            continue
        p = validate(vector)
        top = max(EVENTS, key=lambda k: (p[k], -EVENTS.index(k)))
        out[source] = {"main": top, "main_tr": NAMES[top], "probability_pct": round(100 * p[top], 2)}
    return out

def select_three(experts, rule):
    if not isinstance(experts, dict) or set(experts) != set(SOURCES):
        raise Hakem2Error("THREE_REAL_EXPERTS_REQUIRED_NO_PROXY_FALLBACK")
    parsed = {src: validate(experts[src]) for src in SOURCES}
    joined = {}
    selected = {}
    for family, keys in FAMILIES.items():
        original_name = rule["chosen_by_family"][family]
        source = SOURCE_MAP[original_name]
        selected[family] = source
        for key in keys:
            joined[key] = parsed[source][key]
    ordered = sorted(EVENTS, key=lambda k: (-joined[k], EVENTS.index(k)))
    main = ordered[0]
    main_family = next(f for f, ks in FAMILIES.items() if main in ks)
    alternative = next(k for k in ordered[1:] if k not in FAMILIES[main_family])
    return {
        "ana_tercih": main, "ana_tercih_tr": NAMES[main],
        "hakem_arastirma_yuzdesi": round(100 * joined[main], 2),
        "alternatif_tercih": alternative, "alternatif_tr": NAMES[alternative],
        "alternatif_yuzdesi": round(100 * joined[alternative], 2),
        "tum_7_hakem_yuzdeleri": {k: round(100*joined[k], 2) for k in EVENTS},
        "hakem2_selected_by_family": selected,
        "hakem2_main_source": selected[main_family],
        "classification": "THREE_REAL_EXPERTS_HAKEM2_FROZEN_SELECTOR_RESEARCH_ONLY",
        "model_surum": "HAKEM2_504_TRAIN_FROZEN_V1",
        "warning": "Proxy odds training was NOT on actual iddaa; no proven betting edge or official prematch seal."
    }

def apply_hakem2(result, rule):
    """Decorate an existing in-memory Serbest-V2 batch, retaining legacy read-only.

    Incomplete sources -> show individual forecasts only; no H2 verdict.
    Keep one-source original engine's separate direct choice, clearly labeled.
    """
    if result.get("schema") != "SERBEST_ANALIZ_MODULER_V1":
        raise Hakem2Error("UNSUPPORTED_DAILY_BATCH_SCHEMA")
    for row in result["matches"]:
        experts = row.get("experts", {})
        row["uzman_ayri_tercihler"] = direct_recommendations(experts)
        if row.get("status") != "ANALYSIS_AVAILABLE":
            row["hakem2"] = {"status": "NO_VERIFIED_ANALYSIS"}
            continue
        if set(experts) != set(SOURCES):
            missing = [s for s in SOURCES if s not in experts]
            row["hakem2"] = {"status": "WAITING_ALL_THREE_EXPERTS",
                             "missing_experts": missing}
            if len(experts) == 2:
                row["decision"] = None  # no accidental legacy weighted two-expert verdict
                row["notes"] = list(row.get("notes", [])) + ["HAKEM2_NEVER_BLENDS_TWO_EXPERTS"]
            elif len(experts) == 1 and row.get("decision"):
                row["decision"]["classification"] = "ONE_SOURCE_DIRECT_NOT_HAKEM2"
            continue
        if (row.get("piyasa", {}).get("estimated_quotes") or
            any(set(v) != set(EVENTS) or any(v[k] is None for k in EVENTS)
                for v in experts.values())):
            row["hakem2"] = {"status": "BLOCKED_PARTIAL_OR_THEORETICAL_ODDS"}
            row["decision"] = None
            continue
        result_h2 = select_three(experts, rule)
        row["legacy_v1_comparison_only"] = row.get("decision")
        row["decision"] = result_h2
        row["hakem2"] = {"status": "THREE_SOURCE_SELECTOR_RESEARCH_READY",
                         "selected_by_family": result_h2["hakem2_selected_by_family"]}
    result["referee_mode"] = "HAKEM2_FROZEN_504_RESEARCH_ONLY"
    result["referee_provenance"] = "504 historical proxy-training matches, not live-calibrated iddaa"
    return result
