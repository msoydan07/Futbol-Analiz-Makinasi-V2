#!/usr/bin/env python3
# coding: utf-8
import unittest
from HAKEM2_GUNLUK_SECICI_V1 import (load_h2_rule,select_three,apply_hakem2,Hakem2Error)
from pathlib import Path

RULE=Path(__file__).with_name("hakem2_kural_504_v1.json")
MARKET={"MS1":.42,"MSX":.30,"MS2":.28,"OVER_2.5":.55,"UNDER_2.5":.45,"BTTS_YES":.60,"BTTS_NO":.40}
FOOTBALL={"MS1":.51,"MSX":.24,"MS2":.25,"OVER_2.5":.70,"UNDER_2.5":.30,"BTTS_YES":.47,"BTTS_NO":.53}
MEMORY={"MS1":.45,"MSX":.28,"MS2":.27,"OVER_2.5":.47,"UNDER_2.5":.53,"BTTS_YES":.72,"BTTS_NO":.28}
def experts():
    return {"M4_C3_V4":dict(FOOTBALL),"P0":dict(MARKET),"HAFIZA":dict(MEMORY)}
def batch(ex):
    return {"schema":"SERBEST_ANALIZ_MODULER_V1","matches":[
       {"status":"ANALYSIS_AVAILABLE","match":"Team A - Team B",
        "experts":ex,"notes":[],"decision":{"model_surum":"LEGACY_V1"}}]}

class Hakem2DailyTests(unittest.TestCase):
    def setUp(self):self.rule=load_h2_rule(RULE)
    def test_frozen_rule_p0_in_all_families(self):
        self.assertEqual(set(self.rule["chosen_by_family"].values()),{"ARSIV_P0_PROXY"})
    def test_selector_does_not_blend(self):
        d=select_three(experts(),self.rule)
        self.assertEqual(d["ana_tercih"],"BTTS_YES")
        self.assertEqual(d["hakem_arastirma_yuzdesi"],60.)
        self.assertEqual(d["alternatif_tercih"],"OVER_2.5")
        self.assertEqual(d["alternatif_yuzdesi"],55.)
    def test_real_three_replaces_v1_and_keeps_it_for_comparison(self):
        result=apply_hakem2(batch(experts()),self.rule)["matches"][0]
        self.assertEqual(result["decision"]["model_surum"],"HAKEM2_504_TRAIN_FROZEN_V1")
        self.assertEqual(result["legacy_v1_comparison_only"]["model_surum"],"LEGACY_V1")
    def test_two_never_blend_or_fake_third(self):
        ex=experts();del ex["M4_C3_V4"]
        d=apply_hakem2(batch(ex),self.rule)["matches"][0]
        self.assertIsNone(d["decision"])
        self.assertEqual(d["hakem2"]["status"],"WAITING_ALL_THREE_EXPERTS")
        self.assertEqual(len(d["uzman_ayri_tercihler"]),2)
    def test_one_is_direct_not_referee(self):
        d=apply_hakem2(batch({"M4_C3_V4":FOOTBALL}),self.rule)["matches"][0]
        self.assertEqual(d["decision"]["classification"],"ONE_SOURCE_DIRECT_NOT_HAKEM2")
    def test_theoretical_price_blocks_referee(self):
        d=batch(experts());d["matches"][0]["piyasa"]={"estimated_quotes":{"MS1":{"theoretical_odds":1.51}}}
        r=apply_hakem2(d,self.rule)["matches"][0]
        self.assertIsNone(r["decision"])
        self.assertEqual(r["hakem2"]["status"],"BLOCKED_PARTIAL_OR_THEORETICAL_ODDS")
    def test_invalid_probabilities_block(self):
        ex=experts();ex["P0"]["MS1"]=.99
        with self.assertRaises(ValueError):select_three(ex,self.rule)
    def test_fabricated_source_blocks(self):
        ex=experts();ex["UNKNOWN"]=ex.pop("HAFIZA")
        with self.assertRaises(Hakem2Error):select_three(ex,self.rule)
class DailyEntryTests(unittest.TestCase):
    def test_default_and_explicit_legacy_in_both_cli_paths(self):
        from unittest.mock import patch
        import sys
        import GUNLUK_SERBEST_ANALIZ_KAPISI_V2 as gate
        import SERBEST_ANALIZ_YONLENDIRICI_V1 as router
        for module in (gate,router):
            for legacy in (False,True):
                sample=batch(experts())
                sample["matches"][0]["decision"]["ana_tercih_tr"]="KG Var"
                sample.update(mode="PDF",count=1)
                args=["cli","--pdf","sample.pdf","--rule","old.json","--out-dir","unused"]
                if legacy:args.append("--legacy-hakem1")
                with patch.object(sys,"argv",args),patch.object(module,"load_weights",return_value=({},None)),patch.object(module,"run_pdf",return_value=sample),patch.object(module,"save_run",return_value=("a","b")) as saved:
                    module.main()
                    row=saved.call_args.args[0]["matches"][0]
                    self.assertEqual(row["decision"]["model_surum"],"LEGACY_V1" if legacy else "HAKEM2_504_TRAIN_FROZEN_V1")
    def test_two_experts_in_report_are_separate(self):
        from SERBEST_ANALIZ_YONLENDIRICI_V1 import format_md
        ex=experts();del ex["M4_C3_V4"]
        d=batch(ex);d.update(mode="PDF",count=1)
        report=format_md(apply_hakem2(d,load_h2_rule(RULE)))
        self.assertIn("P0:",report)
        self.assertIn("HAFIZA:",report)
        self.assertIsNone(d["matches"][0]["decision"])

if __name__=="__main__":unittest.main()
