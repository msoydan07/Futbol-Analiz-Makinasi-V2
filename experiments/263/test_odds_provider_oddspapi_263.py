"""Documented OddsPapi v4 fixture/market schema. Purely SYNTHETIC prices."""
import copy,unittest
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from test_four_model_value_policy_263 import fixture,seal
from odds_provider_oddspapi_263 import (match_fixture,normalize_market_catalog,
  build_observation,fetch_for_forecast,QuoteBlocked,cleanname,
  expected_verified_team_names)
from four_model_value_policy_263 import decide
from classification_odds_263 import odds_evidence
NOW=datetime(2026,11,6,16,3,tzinfo=timezone.utc)
def make():
    f,b,lock=fixture()
    # Real SHA-verified 2026/27 TUR1 UUIDs, but wholly synthetic bookmaker prices.
    f["fixture"]["home_id"]="da9ddb8a-aabc-5492-a4b5-b52eaed65165"  # Gaziantep
    f["fixture"]["away_id"]="41b9043e-2819-52dc-963f-a5756b6e88c3"  # Kasimpasa
    seal(f)
    b["forecast_sha256"]=f["payload_sha256"];seal(b)
    fx=f["fixture"]
    fixture_provider={"fixtureId":"id123456789","sportId":10,"statusId":0,"hasOdds":True,
      "startTime":fx["kickoff_utc"],"participant1Name":"Gaziantep FK",
      "participant2Name":"Kasımpaşa","participant1ShortName":"Gaziantep",
      "participant2ShortName":"Kasimpasa"}
    catalog=[]
    for mid,name,handicap,names in [(101,"Full Time Result",0,["1","X","2"]),
         (104,"Both Teams To Score",0,["Yes","No"]),
         (111,"Over Under Full Time",1.5,["Over","Under"]),
         (112,"Over Under Full Time",2.5,["Over","Under"]),
         (113,"Over Under Full Time",3.5,["Over","Under"])]:
        catalog.append({"marketId":mid,"marketName":name,"sportId":10,
            "playerProp":False,"period":"fulltime","handicap":handicap,
            "outcomes":[{"outcomeId":mid*10+i,"outcomeName":n} for i,n in enumerate(names)]})
    options={101:[1.99,3.1,5.4],104:[1.9,1.95],111:[1.1,6.5],
             112:[2.01,1.82],113:[2.45,1.65]}
    markets={}
    for entry in catalog:
        mid=entry["marketId"]
        markets[str(mid)]={"marketActive":True,"outcomes":{
           str(o["outcomeId"]):{"players":{"0":{"active":True,
              "price":options[mid][i],"changedAt":"2026-11-06T16:00:00+00:00"}}}
           for i,o in enumerate(entry["outcomes"])}}
    odds={"fixtureId":"id123456789","sportId":10,"statusId":0,
          "updatedAt":"2026-11-06T16:01:00+00:00",
          "bookmakerOdds":{"iddaa":{"bookmakerIsActive":True,"suspended":False,
            "fixturePath":"https://www.iddaa.com/synthetic-fixture-only","markets":markets}}}
    return f,b,lock,fixture_provider,catalog,odds
class ApiSourceValidation(unittest.TestCase):
    def test_five_market_groups_and_decision(self):
        f,b,l,fixture_doc,catalog,odds=make()
        self.assertEqual(match_fixture(f,[fixture_doc],NOW)["fixtureId"],"id123456789")
        obs=build_observation(f,fixture_doc,odds,catalog,NOW)
        self.assertEqual(set(obs["quotes"]),{"MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5"})
        self.assertEqual(obs["evidence_scope"],"AGGREGATOR_API_NOT_DIRECT_BOOKMAKER_VERIFIED")
        val=decide(f,b,l,obs,now=NOW)
        self.assertIn("AGGREGATOR_SOURCED",val["quote_status"])
        self.assertIsNotNone(val["main_candidate"])
        self.assertFalse(val["betting_authorized"])
        self.assertFalse(val["quote_reverified_by_code"])
        self.assertNotEqual(obs["source_review"]["method"],"MANUAL_PUBLIC_PAGE")
    def test_real_uuid_matches_locked_aliases_not_uuid_string(self):
        f,b,l,fixture_doc,*_=make()
        ids=expected_verified_team_names(f)
        self.assertIn("gaziantep",ids[0])
        self.assertIn("kasimpasa",ids[1])
        self.assertEqual(cleanname("Kasımpaşa"),"kasimpasa")
        self.assertEqual(cleanname("İSTANBUL"),"istanbul")
        self.assertEqual(match_fixture(f,[fixture_doc],NOW)["fixtureId"],"id123456789")
        fake=copy.deepcopy(fixture_doc)
        fake["participant1Name"]=f["fixture"]["home_id"]
        fake["participant1ShortName"]=f["fixture"]["home_id"]
        fake["participant2Name"]=f["fixture"]["away_id"]
        fake["participant2ShortName"]=f["fixture"]["away_id"]
        with self.assertRaisesRegex(QuoteBlocked,"NO_UNIQUE"):
            match_fixture(f,[fake],NOW)
    def test_unknown_uuid_and_wrong_league_fail_closed(self):
        f,b,l,fixture_doc,*_=make()
        unknown=copy.deepcopy(f)
        unknown["fixture"]["home_id"]="00000000-0000-0000-0000-000000000001"
        with self.assertRaisesRegex(QuoteBlocked,"FORECAST_TEAMS_NOT_IN_VERIFIED_LEAGUE_SEASON"):
            match_fixture(unknown,[fixture_doc],NOW)
        wrong=copy.deepcopy(f)
        wrong["fixture"]["league"]="ENG1"
        with self.assertRaisesRegex(QuoteBlocked,"FORECAST_TEAMS_NOT_IN_VERIFIED_LEAGUE"):
            match_fixture(wrong,[fixture_doc],NOW)
    def test_fixture_request_filters_requested_restricted_bookmaker(self):
        f,b,l,fixture_doc,catalog,odds=make()
        calls=[]
        def fake(endpoint,key,params):
            calls.append((endpoint,dict(params)))
            return {"fixtures":[fixture_doc],"markets":catalog,"odds":odds}[endpoint]
        fetch_for_forecast(f,"SYNTHETIC_TEST_ONLY",now=NOW,getter=fake)
        self.assertEqual(calls[0][0],"fixtures")
        self.assertEqual(calls[0][1]["bookmakers"],"iddaa")
    def test_restricted_no_key_stops_without_network(self):
        f,*_=make()
        with self.assertRaisesRegex(QuoteBlocked,"NO_ODDSPAPI_KEY"):
            fetch_for_forecast(f,None,now=NOW)
    def test_same_kickoff_wrong_team_or_swapped_rejected(self):
        f,b,l,fixture_doc,*_=make()
        x=copy.deepcopy(fixture_doc);x["participant1Name"]="WRONG";x["participant1ShortName"]="WRONG"
        with self.assertRaisesRegex(QuoteBlocked,"NO_UNIQUE"):
            match_fixture(f,[x],NOW)
        x=copy.deepcopy(fixture_doc)
        x["participant1Name"],x["participant2Name"]=x["participant2Name"],x["participant1Name"]
        x["participant1ShortName"],x["participant2ShortName"]=x["participant2ShortName"],x["participant1ShortName"]
        with self.assertRaisesRegex(QuoteBlocked,"NO_UNIQUE"):match_fixture(f,[x],NOW)
    def test_same_teams_wrong_kickoff_rejected(self):
        f,b,l,fixture_doc,*_=make()
        x=copy.deepcopy(fixture_doc);x["startTime"]="2026-11-06T20:00:00+00:00"
        with self.assertRaisesRegex(QuoteBlocked,"NO_UNIQUE"):match_fixture(f,[x],NOW)
    def test_duplicate_provider_market_id_rejected(self):
        f,b,l,fixture_doc,catalog,odds=make()
        x=copy.deepcopy(catalog[0]);x["marketId"]=909;catalog.append(x)
        obs=build_observation(f,fixture_doc,odds,catalog,NOW)
        self.assertNotIn("MS",obs["quotes"])
    def test_suspended_iddaa_rejected(self):
        f,b,l,fixture_doc,catalog,odds=make()
        odds["bookmakerOdds"]["iddaa"]["suspended"]=True
        with self.assertRaisesRegex(QuoteBlocked,"NOT_ACTIVE"):
            build_observation(f,fixture_doc,odds,catalog,NOW)
    def test_missing_odds_side_drops_only_incomplete_group(self):
        f,b,l,fixture_doc,catalog,odds=make()
        odds["bookmakerOdds"]["iddaa"]["markets"]["111"]["outcomes"].pop("1111")
        obs=build_observation(f,fixture_doc,odds,catalog,NOW)
        self.assertNotIn("GOALS_1.5",obs["quotes"])
        self.assertIn("MS",obs["quotes"])
    def test_bad_source_or_stale_event_rejected(self):
        f,b,l,fixture_doc,catalog,odds=make()
        odds["bookmakerOdds"]["iddaa"]["fixturePath"]="https://other.example/synthetic"
        with self.assertRaisesRegex(QuoteBlocked,"DIRECT_FIXTURE_LINK"):
            build_observation(f,fixture_doc,odds,catalog,NOW)
        odds["bookmakerOdds"]["iddaa"]["fixturePath"]="https://www.iddaa.com/synthetic"
        odds["updatedAt"]="2026-11-06T15:01:00+00:00"
        with self.assertRaisesRegex(QuoteBlocked,"STALE"):
            build_observation(f,fixture_doc,odds,catalog,NOW)
    def test_human_price_cannot_be_labeled_api_accidentally(self):
        f,b,l,fixture_doc,catalog,odds=make()
        obs=build_observation(f,fixture_doc,odds,catalog,NOW)
        obs["source_review"]["method"]="MANUAL_PUBLIC_PAGE";seal(obs)
        with self.assertRaisesRegex(ValueError,"PROVENANCE_INVALID"):
            decide(f,b,l,obs,now=NOW)
    def test_api_iddaa_secrets_not_in_output(self):
        f,b,l,fixture_doc,catalog,odds=make()
        fake=lambda endpoint,key,params:{"fixtures":[fixture_doc],"markets":catalog,"odds":odds}[endpoint]
        o=fetch_for_forecast(f,"PRIVATE_SYNTHETIC_API_KEY",now=NOW,getter=fake)
        self.assertNotIn("PRIVATE_SYNTHETIC_API_KEY",str(o))
        self.assertEqual(o["source_domain"],"iddaa.com")
    def test_precommit_late_or_single_sided_provider_blocked(self):
        import json,tempfile
        from pathlib import Path
        from odds_provider_oddspapi_263 import verify_precommit
        f,b,l,fx,cat,book=make()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            forecast_file=root/"forward_quad_263"/"2026-11-06"/("a"*24+".json")
            forecast_file.parent.mkdir(parents=True)
            forecast_file.write_text(json.dumps(f))
            report=root/"report.json"
            report.write_text(json.dumps({"schema":"quad_named_match_batch_report_v1",
                "outcomes":[{"status":"REGISTERED_FOUR_MODELS_EXPERIMENTAL",
                            "path":str(forecast_file)}]}))
            ob=root/"quotes";de=root/"decisions"
            self.assertEqual(verify_precommit(report,now=NOW,
                observation_dir=ob,decision_dir=de),0)
            obs=build_observation(f,fx,book,cat,NOW)
            from four_model_value_policy_263 import decide
            d=decide(f,b,l,obs,now=NOW)
            qpath=ob/"2026-11-06"/("a"*24+".json")
            qpath.parent.mkdir(parents=True)
            qpath.write_text(json.dumps(obs))
            with self.assertRaisesRegex(QuoteBlocked,"SINGLE_SIDED"):
                verify_precommit(report,now=NOW,observation_dir=ob,decision_dir=de)
            dpath=de/"2026-11-06"/("a"*24+".json")
            dpath.parent.mkdir(parents=True)
            dpath.write_text(json.dumps(d))
            self.assertEqual(verify_precommit(report,now=NOW,
                observation_dir=ob,decision_dir=de),1)
            later=NOW+timedelta(minutes=11)
            with self.assertRaisesRegex(QuoteBlocked,"NOW_STALE"):
                verify_precommit(report,now=later,observation_dir=ob,decision_dir=de)
            after=NOW+timedelta(hours=1)
            with self.assertRaisesRegex(QuoteBlocked,"NOT_PREMATCH"):
                verify_precommit(report,now=after,observation_dir=ob,decision_dir=de)

if __name__=="__main__":unittest.main()
