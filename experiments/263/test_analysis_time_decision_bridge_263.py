"""NEW C2/ABC/report-join only; not M4 or historical performance rerun."""
import unittest
from datetime import datetime,timezone
from analysis_time_decision_bridge_263 import offline_appendix,render_appendix,BridgeError
from classification_odds_263 import poisson_market

NOW=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
LEAGUE="TUR1";HOME="home-test-id";AWAY="away-test-id";DAY="2026-11-08"


def samples(*,c2=True):
    fixture={"status":"READY_FOR_DATA_AUDIT","fixture":{
        "league":LEAGUE,"home_id":HOME,"away_id":AWAY,"local_date":DAY,
        "kickoff_utc":"2026-11-08T18:00:00+00:00",
        "source_url":"https://www.tff.org/fixture/test"},
        "facts":{"lineups":{"status":"NOT_CHECKED"}}}
    model=None
    if c2:
        model={"details":{"lambda_home":2.2,"lambda_away":.7},
               "goals":{"lambda_home":2.2,"lambda_away":.7,
                        "markets":poisson_market(2.2,.7)}}
    case={"identity":{"league":LEAGUE,"home_id":HOME,"away_id":AWAY,"target_date":DAY},
          "analysis":{"model_outputs":{"C2":model}},
          "decision_preflight_263":{"canonical_model":"C2" if c2 else None}}
    bundle={"scope":"HYPOTHETICAL_OFFLINE_AUDIT","not_live_match_analysis":True,
            "real_fixture_verified":False,"recommendations":[],"odds_EV":None,
            "cases":[case]}
    return fixture,bundle


class ReportConnection(unittest.TestCase):
    def test_full_14_c2_markets_appendix_all_missing_odds_explicit(self):
        ctx,bundle=samples()
        x=offline_appendix(ctx,bundle,NOW)
        self.assertEqual(len(x["rows"]),14)
        self.assertEqual(x["lineups"],"NOT_CHECKED")
        self.assertFalse(x["lineups_not_published_blocks_math"])
        self.assertTrue(all(r["EV"] is None and r["official_class"] is None and
                           r["candidate_class"]=="DEGERLENDIRILEMEDI"
                           for r in x["rows"]))
        self.assertIn("§12–14",render_appendix(x))
        self.assertIn("DOĞRULANAMADI",render_appendix(x))
        self.assertFalse(x["pilot_registered"])

    def test_missing_c2_does_not_promote_B_C3_M4(self):
        x=offline_appendix(*samples(c2=False),NOW)
        self.assertEqual(x["rows"],[])
        self.assertEqual(x["model"],"C2_CANONICAL_ONLY_NO_FALLBACK")
        self.assertEqual(x["comparators_not_promoted"],["B","C3","M4"])

    def test_wrong_official_match_cannot_decorate_wrong_prediction(self):
        ctx,bundle=samples()
        ctx["fixture"]["home_id"]="other"
        with self.assertRaisesRegex(BridgeError,"identity"):
            offline_appendix(ctx,bundle,NOW)

    def test_no_official_gate_or_offline_contract_tamper(self):
        ctx,bundle=samples()
        ctx["status"]="NOT_VERIFIED"
        with self.assertRaisesRegex(BridgeError,"official"):
            offline_appendix(ctx,bundle,NOW)
        ctx,bundle=samples()
        bundle["real_fixture_verified"]=True
        with self.assertRaisesRegex(BridgeError,"contract"):
            offline_appendix(ctx,bundle,NOW)

    def test_no_past_kickoff_approval(self):
        with self.assertRaisesRegex(BridgeError,"prematch"):
            offline_appendix(*samples(),datetime(2026,11,9,tzinfo=timezone.utc))


    def test_trusted_current_quote_reports_source_time_without_official_grade(self):
        context,bundle=samples()
        f=context["fixture"]
        k=f["league"]+":"+f["home_id"]+":"+f["away_id"]+":"+f["local_date"]
        q={"fixture_key":k,"market_group":"MS","verification":"INDEPENDENTLY_CHECKED",
           "stage":"PREMATCH","source":"EXAMPLE_TEST_ONLY",
           "source_url":"https://example.org/synthetic",
           "checked_at_utc":NOW.isoformat(),
           "decimal_odds":{"MS1":1.50,"MSX":4.20,"MS2":7.90}}
        calls=[]
        def provider(fixture):
            calls.append(fixture["home_id"])
            return {"MS1":q}
        result=offline_appendix(context,bundle,NOW,quote_provider=provider)
        self.assertEqual(calls,[HOME])
        self.assertEqual(result["observed_selection_prices"],1)
        self.assertEqual(result["mathematical_EV_calculations"],1)
        p=next(r for r in result["rows"] if r["selection"]=="MS1")
        self.assertEqual(p["price"]["decimal_odds"],1.50)
        self.assertEqual(p["candidate_class"],"DEGERLENDIRILEMEDI")
        self.assertIsNone(p["official_class"])
        self.assertIn("1.50 (EXAMPLE_TEST_ONLY",render_appendix(result))
        self.assertFalse(result["pilot_registered"])

    def test_no_untrusted_json_or_fake_market_injection(self):
        context,bundle=samples()
        with self.assertRaisesRegex(BridgeError,"callable_required"):
            offline_appendix(context,bundle,NOW,quote_provider={"MS1":1.50})
        with self.assertRaisesRegex(BridgeError,"invalid_return"):
            offline_appendix(context,bundle,NOW,quote_provider=lambda _:None)
        with self.assertRaisesRegex(BridgeError,"unrecognized_quote_market"):
            offline_appendix(context,bundle,NOW,quote_provider=lambda _:{"invented_market":{}})

if __name__=="__main__":
    unittest.main()
