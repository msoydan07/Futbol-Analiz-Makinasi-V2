"""One-shot contract checks. Tests intentionally use a temporary copy, never old seals."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from check_active_decisions_263 import ROOT, ActiveDecisionConflict, verify_active_policy

NEEDED = (
    "docs/263_AKTIF_KARARLAR.json",
    "experiments/263/iddaa_pdf_one_step_263.py",
    "experiments/263/model_first_iddaa_bridge_263.py",
    "experiments/263/model_first_decision_263.py",
    "experiments/263/model_first_selection_lock_20261120_normal_v3.json",
    "experiments/263/model_first_selection_lock_20261121_v4.json",
    "experiments/263/model_first_frozen_c3_calibration_263.py",
    "experiments/263/sabah_batch_263.py",
    "experiments/263/iddaa_pdf_approved_layout_263.py",
    "experiments/263/sabah_mobile_model_only_263.py",
    "docs/263_TOPLU_RAPOR_KALICI_KART_SABLONU_20261121.md",
    "experiments/263/normal_historical_reference_263.py",
    "experiments/263/m4_integrated.py",
    ".github/workflows/263-sabah-new100-on-request.yml",
    "experiments/263/historical_probability_reliability_263.py",
    # Single-screen official layout, append-only second PDF archive.
    # Test temporary copies must include ALL files required by guard.
    "experiments/263/iddaa_pdf_last_review_263.py",
    "experiments/263/second_pdf_commentary_archive_263.py",
    "docs/263_IKINCI_PDF_TEKLI_RAPOR_KALICI_SABLON_20261121.md",
    "docs/263_IKINCI_PDF_ORAN_YORUM_ARSIV_KARARI_20261121.md",
)

class Contract(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory()
        self.root=Path(self.work.name)
        for rel in NEEDED:
            dst=self.root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/rel,dst)
    def tearDown(self):
        self.work.cleanup()
    def test_current_single_source_passes(self):
        result=verify_active_policy(self.root)
        self.assertEqual(result["status"],"ACTIVE_DECISIONS_OK")
        self.assertEqual(result["active_topics"],8)
        self.assertEqual(result["market"],"USER_IDDAA_PDF_ONLY_FIFTH_REFERENCE")
    def test_same_topic_two_active_decisions_blocks(self):
        path=self.root/NEEDED[0]
        d=json.loads(path.read_text(encoding="utf-8"))
        d["active"].append(dict(d["active"][0]))
        path.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_old_price_decider_reactivated_blocks(self):
        path=self.root/NEEDED[1]
        text=path.read_text(encoding="utf-8").replace(
            "from model_first_iddaa_bridge_263 import calibrate_session",
            "from iddaa_pdf_value_bridge_263 import calibrate_session")
        path.write_text(text,encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_wrong_expert_policy_blocks(self):
        path=self.root/"experiments/263/model_first_selection_lock_20261121_v4.json"
        d=json.loads(path.read_text(encoding="utf-8"))
        d["family_anchors"]["KG"]="M4"
        path.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_pinnacle_reactivation_in_workflow_blocks(self):
        path=self.root/".github/workflows/263-sabah-new100-on-request.yml"
        path.write_text(path.read_text(encoding="utf-8")+"\\nTHE_ODDS_API_KEY: forbidden\\n",
                        encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_external_price_reference_reactivated_blocks(self):
        path=self.root/NEEDED[0]
        d=json.loads(path.read_text(encoding="utf-8"))
        d["canonical_entrypoints"]["new100_price_reference"]="experiments/263/sabah_pinnacle_new100_bridge_263.py"
        path.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_unapproved_model_only_batch_renderer_blocks(self):
        path=self.root/"experiments/263/sabah_mobile_model_only_263.py"
        contents=path.read_text(encoding="utf-8")
        contents=contents.replace(
            'render_model_only_batch(report["day_turkey"],rows,folder/"toplu.pdf")',
            'batch_pdf(folder/"toplu.pdf",report["day_turkey"],rows)')
        path.write_text(contents,encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_template_spec_missing_blocks(self):
        (self.root/"docs/263_TOPLU_RAPOR_KALICI_KART_SABLONU_20261121.md").unlink()
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_xg_in_main_model_blocks(self):
        path=self.root/"experiments/263/m4_integrated.py"
        path.write_text(path.read_text(encoding="utf-8")+"\n# xg added\n",encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)

if __name__=="__main__":
    unittest.main()
