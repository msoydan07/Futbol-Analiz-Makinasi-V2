import unittest
from datetime import date
from uefa_asof_domestic_input_audit_263 import measure,xg_pair,AuditError,load_inputs
def r(d,team,lg="ENG1",season="2025-2026",xg=False):
    x={"_date":date.fromisoformat(d),"match_date":d,"home_id":team,
      "away_id":"OTHER","league":lg,"season":season}
    if xg:x.update(home_xg="1.2",away_xg="0.8")
    return x
def f(d="2025-10-10"):
    return {"competition":"UEFA_CL","date":d,"home_club_id_candidate":"H",
      "away_club_id_candidate":"A","home_league":"ENG1","away_league":"TUR1"}
class TimeSafety(unittest.TestCase):
    def test_no_same_day_future_data(self):
        s,rows=measure([r("2025-10-09","H"),r("2025-10-10","H"),
          r("2025-10-11","H"),r("2025-10-09","A","TUR1")],[f()])
        self.assertEqual(rows[0]["asof_domestic_matches"]["home"]["prior_match_count"],1)
        self.assertFalse(rows[0]["model_eligible"])
    def test_thresholds_never_promote_model(self):
        rows=[r("2025-09-%02d"%i,team,lg,xg=True)
              for i in range(1,9) for team,lg in (("H","ENG1"),("A","TUR1"))]
        s,res=measure(rows,[f()])
        self.assertTrue(res[0]["both_4_goals"])
        self.assertTrue(res[0]["both_8_goals"])
        self.assertTrue(res[0]["both_4_xg_pairs"])
        self.assertFalse(s["model_training_allowed"])
    def test_wrong_league_or_season_not_counted(self):
        _,res=measure([r("2025-09-01","H","TUR1"),
                 r("2025-09-01","H","ENG1","2026-2027")],[f()])
        self.assertEqual(res[0]["asof_domestic_matches"]["home"]["prior_match_count"],0)
    def test_no_fake_xg_missing(self):
        self.assertFalse(xg_pair(r("2025-09-01","H")))
    def test_source_sha_is_frozen(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            h=Path(d)/"hist";u=Path(d)/"union"
            h.write_text("untrusted");u.write_text("{}")
            with self.assertRaisesRegex(AuditError,"SHA_MISMATCH"):
                load_inputs(h,u)
if __name__=="__main__":unittest.main()
