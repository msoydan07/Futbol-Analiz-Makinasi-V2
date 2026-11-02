"""New offline UEFA handoff: 10-league scope first; source FACTS not runner verification."""
import copy
import json
import unittest
from datetime import datetime
from pathlib import Path
from uefa_web_evidence_handoff_263 import (
    requested_from_web_evidence,HandoffError,validate_evidence
)
INDEX=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
EVIDENCE=json.loads(Path("experiments/263/evidence/uefa_web_2026-11-02_review_only.json").read_text(encoding="utf-8"))
NOW=datetime.fromisoformat("2026-11-02T17:00:00+03:00")
class EuropeanWebHandoff(unittest.TestCase):
    def call(self,c,h,a,**kw):
        return requested_from_web_evidence(c,h,a,index=INDEX,now=NOW,
                                           evidence=EVIDENCE,**kw)
    def test_five_scope_pass_fixtures_confirm_exact_article_facts(self):
        matches=[("UEFA_CL","Galatasaray","Stuttgart","2026-11-03T17:45:00+00:00"),
                 ("UEFA_CL","Barcelona","Aston Villa","2026-11-03T20:00:00+00:00"),
                 ("UEFA_CL","Fenerbahçe","Liverpool","2026-11-04T17:45:00+00:00"),
                 ("UEFA_EL","Crystal Palace","Hoffenheim","2026-11-05T17:45:00+00:00"),
                 ("UEFA_EL","AZ Alkmaar","Juventus","2026-11-05T20:00:00+00:00")]
        for c,h,a,k in matches:
            with self.subTest(h=h,a=a):
                r=self.call(c,h,a)
                self.assertTrue(r["assisted_web_article_evidence_accepted"])
                self.assertEqual(r["fixture"]["kickoff_utc"],k)
                self.assertFalse(r["live_automated_UEFA_verification"])
                self.assertFalse(r["model_forecast_authorized"])
                self.assertFalse(r["pilot_recorded"])
    def test_celtic_scope_skip_prevents_even_evidence_file_read(self):
        calls=[]
        r=requested_from_web_evidence("UEFA_EL","Celtic","Beşiktaş",index=INDEX,now=NOW,
                                     evidence_loader=lambda:calls.append("opened"))
        self.assertFalse(r["assisted_web_article_evidence_accepted"])
        self.assertEqual(calls,[])
        self.assertEqual(r["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
    def test_old_review_is_rejected(self):
        old=NOW.replace(day=6)
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=old,evidence=EVIDENCE)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
        self.assertEqual(r["evidence_rejection_reason"],"WEB_EVIDENCE_STALE_OR_FROM_FUTURE")
    def test_future_date_is_rejected(self):
        data=copy.deepcopy(EVIDENCE);data["checked_on_istanbul"]="2026-11-03"
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,evidence=data)
        self.assertEqual(r["evidence_rejection_reason"],"WEB_EVIDENCE_STALE_OR_FROM_FUTURE")
    def test_wrong_website_is_not_accepted(self):
        data=copy.deepcopy(EVIDENCE)
        data["sources"]["UEFA_CL"]["source_url"]="https://www.uefa.com.evil.test/fixtures"
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,evidence=data)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
    def test_same_match_in_other_competition_not_accepted(self):
        r=self.call("UEFA_EL","Barcelona","Aston Villa")
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
    def test_official_page_result_line_cannot_be_upgraded_to_future_match(self):
        data=copy.deepcopy(EVIDENCE)
        data["fixtures"][1]["fixture_line"]="Barcelona 3-0 Aston Villa"
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,evidence=data)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
    def test_no_unknown_or_made_up_extra_fields(self):
        data=copy.deepcopy(EVIDENCE)
        data["fixtures"][1]["claimed_official_verified"]=True
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=NOW,evidence=data)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
    def test_timezone_and_competition_not_guessed(self):
        r=self.call("UEFA_EL","AZ Alkmaar","Juventus")
        self.assertEqual(r["fixture"]["kickoff_basis"],"PUBLISHED_UEFA_ARTICLE_DEFAULT_21_CET")
        self.assertEqual(r["fixture"]["competition"],"UEFA_EL")
    def test_future_seven_day_horizon_cannot_be_extended(self):
        too_soon=NOW.replace(day=2,hour=9)
        data=copy.deepcopy(EVIDENCE)
        data["fixtures"][1]["date_line"]="Tuesday 24 November 2026"
        r=requested_from_web_evidence("UEFA_CL","Barcelona","Aston Villa",index=INDEX,now=too_soon,evidence=data)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
    def test_source_index_immutable(self):
        before=copy.deepcopy(INDEX)
        self.call("UEFA_CL","Galatasaray","Stuttgart")
        self.assertEqual(INDEX,before)
if __name__=="__main__":unittest.main()
