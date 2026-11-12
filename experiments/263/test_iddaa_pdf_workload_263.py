"""Offline adversarial exact-source seven-day calendar evidence tests."""
from datetime import datetime,timezone,timedelta
import unittest
from iddaa_pdf_workload_263 import collect_same_page,workload_for_pdf
from iddaa_pdf_team_alias_preflight_263 import index_registry

NOW=datetime(2026,11,21,12,45,tzinfo=timezone.utc)
KICKOFF="2026-11-21T13:00:00+00:00"
SOURCE="https://www.tff.org/Default.aspx?hafta=12&pageId=198"

class OfficialWorkloadTests(unittest.TestCase):
    def setUp(self):
        self.idx,_,_=index_registry()
        self.h=self.idx["TUR1"]["galatasaray"]
        self.a=self.idx["TUR1"]["samsunspor"]
        self.obs={"status":"VERIFIED_OFFICIAL_FIXTURE",
            "source_url":SOURCE,"retrieved_at_utc":NOW.isoformat()}
        self.ver={"source_url":SOURCE,
                  "retrieved_at_utc":NOW.isoformat(),"kickoff_utc":KICKOFF}

    def event(self,home,away,day):
        return {"home":home,"away":away,
                "kickoff_utc":day,"format":"tff_2026_week12"}

    def test_verified_requested_at_7days_not_kickoff_shift(self):
        inside=(NOW+timedelta(days=7)).isoformat()
        too_late=(NOW+timedelta(days=7,seconds=1)).isoformat()
        earlier=(NOW-timedelta(days=2)).isoformat()
        raw=[
            self.event("GALATASARAY A.Ş.","SAMSUNSPOR A.Ş.",KICKOFF),
            self.event("GALATASARAY A.Ş.","FENERBAHÇE A.Ş.",inside),
            self.event("FENERBAHÇE A.Ş.","GALATASARAY A.Ş.",earlier),
            self.event("SAMSUNSPOR A.Ş.","FENERBAHÇE A.Ş.",too_late),
        ]
        proof=collect_same_page("TUR1",self.h,self.a,raw,
            source_url=SOURCE,retrieved_at_utc=NOW.isoformat(),
            source_payload="some official round HTML",index=self.idx)
        self.obs["adjacent_league_evidence"]=proof
        output=workload_for_pdf(self.obs,self.ver,"TUR1",self.h,self.a,NOW)
        self.assertEqual(output["status"],"VERIFIED_SAME_PAGE_LEAGUE_PARTIAL")
        self.assertEqual(len(output["teams"][self.h]["next_7_days"]),1)
        self.assertEqual(len(output["teams"][self.h]["past_7_days"]),1)
        self.assertEqual(len(output["teams"][self.a]["next_7_days"]),0)
        self.assertFalse(output["uefa_and_cup_schedule_complete"])
        self.assertFalse(output["model_probabilities_changed"])
        self.assertEqual(output["new_official_network_calls"],0)

    def test_target_game_never_counted_as_extra_future_game(self):
        source=[
            self.event("GALATASARAY A.Ş.","SAMSUNSPOR A.Ş.",KICKOFF)]
        p=collect_same_page("TUR1",self.h,self.a,source,
                 source_url=SOURCE,retrieved_at_utc=NOW.isoformat(),
                 source_payload="fixture html",index=self.idx)
        self.assertEqual(p["verified_adjacent_league_events"],[])
        self.obs["adjacent_league_evidence"]=p
        answer=workload_for_pdf(self.obs,self.ver,"TUR1",self.h,self.a,NOW)
        self.assertEqual(answer["status"],"VERIFIED_SAME_PAGE_LEAGUE_PARTIAL")
        self.assertEqual(answer["teams"][self.h]["next_7_days"],[])
        self.assertEqual(answer["teams"][self.a]["next_7_days"],[])
        self.assertEqual(answer["teams"][self.h]["rotation_label"],"VERI_YETERSIZ")

    def test_conflicting_official_clocks_never_claim_rotation(self):
        raw=[
            self.event("GALATASARAY A.Ş.","FENERBAHÇE A.Ş.",
                       (NOW+timedelta(days=1)).isoformat()),
            self.event("GALATASARAY A.Ş.","FENERBAHÇE A.Ş.",
                       (NOW+timedelta(days=2)).isoformat()),
        ]
        proof=collect_same_page("TUR1",self.h,self.a,raw,source_url=SOURCE,
            retrieved_at_utc=NOW.isoformat(),source_payload="html",index=self.idx)
        self.assertEqual(proof["verified_adjacent_league_events"],[])

    def test_unofficial_source_never_promoted(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_NOT_OFFICIAL"):
            collect_same_page("TUR1",self.h,self.a,[],
                source_url="https://fake.tff.org.evil.invalid",retrieved_at_utc=NOW.isoformat(),
                source_payload="faked",index=self.idx)

    def test_missing_cup_or_unknown_page_is_never_clean_schedule(self):
        item=workload_for_pdf(self.obs,self.ver,"TUR1",self.h,self.a,NOW)
        self.assertEqual(item["status"],"OFFICIAL_ADJACENT_LEAGUE_DATA_UNAVAILABLE")
        self.assertTrue(all(x["rotation_label"]=="VERI_YETERSIZ"
                            for x in item["teams"].values()))

if __name__=="__main__":unittest.main()

