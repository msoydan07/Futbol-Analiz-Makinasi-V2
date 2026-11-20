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
    "experiments/263/model_first_selection_lock_20261120.json",
    "experiments/263/m4_integrated.py",
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
        self.assertEqual(result["active_topics"],7)
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
        path=self.root/"experiments/263/model_first_selection_lock_20261120.json"
        d=json.loads(path.read_text(encoding="utf-8"))
        d["family_anchors"]["KG"]="M4"
        path.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)
    def test_xg_in_main_model_blocks(self):
        path=self.root/"experiments/263/m4_integrated.py"
        path.write_text(path.read_text(encoding="utf-8")+"\n# xg added\n",encoding="utf-8")
        with self.assertRaises(ActiveDecisionConflict):
            verify_active_policy(self.root)

if __name__=="__main__":
    unittest.main()
