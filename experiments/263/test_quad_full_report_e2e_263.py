"""One complete named-match report using the real frozen 4,413-match dataset.

Fixture and odds adapters are SYNTHETIC; nothing below asserts an actual
upcoming fixture or bookmaker quote. No pilot output is created.
"""
import os
import unittest
from pathlib import Path
from datetime import datetime,timezone
from requested_match_runner_263 import requested_match
from test_requested_match_runner_263 import gate,INDEX,ALIASES,EVIDENCE

NOW=datetime(2026,11,2,15,tzinfo=timezone.utc)
HISTORY=Path(os.environ.get("M263_FROZEN_HISTORY","not-supplied.csv"))

class NamedMatchReadOnlyAcceptance(unittest.TestCase):
    def test_one_named_match_four_models_abc_and_market_no_pilot(self):
        self.assertTrue(HISTORY.is_file(),"Frozen historical artifact mandatory; no skip")
        seen=[]
        def synthetic_price(verified_fixture):
            seen.append(verified_fixture["home_id"])
            match=":".join((verified_fixture["league"],verified_fixture["home_id"],
                             verified_fixture["away_id"],verified_fixture["local_date"]))
            snapshot={"fixture_key":match,"market_group":"MS","stage":"PREMATCH",
                "verification":"INDEPENDENTLY_CHECKED","source":"SYNTHETIC_NOT_A_LIVE_PRICE",
                "source_url":"https://example.org/test-only",
                "checked_at_utc":NOW.isoformat(),
                "decimal_odds":{"MS1":1.50,"MSX":4.50,"MS2":7.00}}
            return {"MS1":snapshot}
        status,files=requested_match(
            league="TUR1",home="Galatasaray",away="Konyaspor",
            index_path=INDEX,alias_path=ALIASES,history_path=HISTORY,
            evidence_path=EVIDENCE,now=NOW,fixture_gate=gate,
            quote_provider=synthetic_price,
            include_four_model_market_reference=True)
        self.assertEqual(status["status"],"OFFICIAL_FIXTURE_CHECKED_FROZEN_MATH_PREVIEW_ONLY")
        self.assertFalse(status["live_analysis_accepted"])
        self.assertFalse(status["pilot_recorded"])
        self.assertEqual(len(seen),1)
        self.assertEqual(files["section_acceptance_263.json"]["status"],"PASS_OFFLINE_INTEGRATION_ONLY")
        self.assertEqual(files["model_preview.json"]["recommendations"],[])
        report=files["readonly_four_model_market_reference.json"]
        self.assertEqual(set(report["models"]),{"B","C2","C3","M4"})
        self.assertIn("MS",report["benchmarks"])
        market=report["benchmarks"]["MS"]
        self.assertEqual(market["status"],"DESCRIPTIVE_ONLY_NOT_MODEL_SELECTION")
        self.assertFalse(market["model_selected"])
        self.assertFalse(market["A_B_C_approved"])
        self.assertFalse(report["pilot_recorded"])
        self.assertFalse(report["production_modified"])
        decision=files["analysis_time_odds_abc_appendix.json"]
        self.assertEqual(decision["observed_selection_prices"],1)
        self.assertEqual(decision["approved_classes"],[])
        self.assertIn("Dört modelin ayrı çıktıları",files["model_preview.md"])
        self.assertIn("§12–14",files["model_preview.md"])
        self.assertIn("piyasa referansı",files["model_preview.md"])
        self.assertFalse(Path("forward_quad_263").exists())

if __name__=="__main__":
    unittest.main()
