"""One planned deterministic acceptance: archived beyondELO CSV, never live API."""
import csv
import io
import json
import unittest
from datetime import datetime,timezone
from pathlib import Path
from uefa_ten_league_scope_gate_263 import check_europe_scope
from uefa_elo_reference_263 import (read_json,COHORT,ALIASES,build_crosswalk,
                                   reference_for_match,preflight_elo,EloBridgeError)
from uefa_requested_match_entry_263 import requested_europe_match,SOURCES
IDX=read_json("experiments/263/evidence/identity_index_263.json")
CO=read_json(COHORT)
REV=read_json(ALIASES)
SNAP=Path("data/europe_staged_263/elo_integrity_acceptance/source_csv/current.csv")
FETCHED=datetime.fromisoformat("2026-11-03T05:20:00+00:00")
KO="2026-11-04T20:00:00+00:00"
def fixture(kickoff=KO):
    return {"official_article_directly_fetched":True,"kickoff_utc":kickoff}
def live(bytes_=None):return (bytes_ if bytes_ is not None else SNAP.read_bytes()),FETCHED
def as_csv(rows):
    b=io.StringIO()
    w=csv.DictWriter(b,fieldnames=list(rows[0]),lineterminator="\n")
    w.writeheader();w.writerows(rows)
    return b.getvalue().encode("utf-8")

class EloBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SNAP.read_bytes()
        cls.rows=list(csv.DictReader(io.StringIO(cls.raw.decode("utf-8-sig"))))
    def test_source_pinned_same_old_run_no_refetch_and_all_167_crosswalk(self):
        import hashlib
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),
            "073a461d810396af6ae74216e8d400d5c5d27a654a153014d36dc4a4c7ee8be5")
        result,blocked=build_crosswalk(IDX,CO,REV,self.raw)
        self.assertEqual(len(result),167)
        self.assertEqual(blocked,{})
        self.assertEqual({e["source_identity_level"] for e in result.values()},
            {"NORMALIZED_OFFICIAL_ALIAS","REVIEWED_FEDERATION_NAME_PLUS_PROVIDER_SLUG"})
        counts={typ:sum(e["source_identity_level"]==typ for e in result.values())
                for typ in ("NORMALIZED_OFFICIAL_ALIAS","REVIEWED_FEDERATION_NAME_PLUS_PROVIDER_SLUG")}
        self.assertEqual(counts,{"NORMALIZED_OFFICIAL_ALIAS":134,
                                 "REVIEWED_FEDERATION_NAME_PLUS_PROVIDER_SLUG":33})
        self.assertEqual(len({e["provider_slug"] for e in result.values()}),167)
        self.assertNotIn("ENG2",{e["league"] for e in result.values()})
        self.assertNotIn("ERZURUMSPOR FK",{e["official_name"] for e in result.values()})
        for e in result.values():
            self.assertEqual(e["source_row"]["is_ranked"],"true")
            self.assertGreaterEqual(e["source_row"]["last_match_date"],"2026-10-01")
    def test_mapped_example_is_descriptive_not_poisson_or_betting(self):
        scope=check_europe_scope("Galatasaray","Liverpool",IDX)
        res=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:live(self.raw),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_DESCRIPTIVE_REFERENCE_ATTACHED_NOT_MODEL_CALIBRATED",res)
        self.assertEqual(res["mapped_candidate_count"],167)
        self.assertEqual(res["source_identity_limit"],"NAME_AND_COUNTRY_RECONCILIATION_ONLY_NO_SHARED_UEFA_ID")
        self.assertAlmostEqual(res["home_minus_away_elo"],res["home"]["elo"]-res["away"]["elo"])
        self.assertIsNone(res["elo_1x2_probabilities"])
        self.assertFalse(res["elo_affects_goal_lambda"])
        self.assertFalse(res["model_calibration_approved"])
    def test_manual_review_team_works_with_exact_expected_name(self):
        scope=check_europe_scope("Tottenham Hotspur","Liverpool",IDX)
        res=reference_for_match(scope,fixture(),IDX,CO,REV,source_provider=lambda:live(self.raw),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_DESCRIPTIVE_REFERENCE_ATTACHED_NOT_MODEL_CALIBRATED",res)
        self.assertEqual(res["home"]["provider_slug"],"tottenham-hotspurs")
        self.assertEqual(res["home"]["identity_check"],"REVIEWED_FEDERATION_NAME_PLUS_PROVIDER_SLUG")
    def test_exclusions_never_call_data_source(self):
        for a,b in (("Arsenal","Cardiff City"),("Arsenal","ERZURUMSPOR FK")):
            with self.subTest(a=a,b=b):
                sc=check_europe_scope(a,b,IDX)
                self.assertTrue(sc["allow_further_research"])
                self.assertEqual(preflight_elo(sc,CO),"EUROPE_ELO_COHORT_EXCLUDED")
                got=reference_for_match(sc,fixture(),IDX,CO,REV,
                    source_provider=lambda: self.fail("fetch attempted"),at_utc=FETCHED)
                self.assertEqual(got["status"],"EUROPE_ELO_COHORT_EXCLUDED")
    def test_outside_ten_league_stops_without_data(self):
        sc=check_europe_scope("Arsenal","Celtic",IDX)
        got=reference_for_match(sc,fixture(),IDX,CO,REV,
             source_provider=lambda:self.fail("fetch attempted"),at_utc=FETCHED)
        self.assertEqual(got["status"],"UEFA_SCOPE_BLOCKED")
    def test_future_or_after_kickoff_snapshot_is_not_used(self):
        scope=check_europe_scope("Galatasaray","Liverpool",IDX)
        no=reference_for_match(scope,fixture(kickoff="2026-11-03T01:00:00+00:00"),IDX,CO,REV,
            source_provider=lambda:self.fail("after KO fetched"),at_utc=FETCHED)
        self.assertEqual(no["status"],"MATCH_ALREADY_STARTED_SOURCE_NOT_FETCHED")
        bad=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:(self.raw,datetime.fromisoformat("2026-11-05T00:00:00+00:00")),at_utc=FETCHED)
        self.assertEqual(bad["status"],"ELO_SOURCE_OR_INTEGRITY_NOT_VERIFIED")
    def test_manual_name_drift_stops_that_teams_elo(self):
        rows=[dict(r) for r in self.rows]
        for r in rows:
            if r["slug"]=="tottenham-hotspurs":r["name"]="Unrelated Club"
        raw=as_csv(rows)
        scope=check_europe_scope("Tottenham Hotspur","Liverpool",IDX)
        res=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:live(raw),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_IDENTITY_NOT_VERIFIED",res)
    def test_stale_provider_date_and_last_match_not_usable(self):
        scope=check_europe_scope("Galatasaray","Liverpool",IDX)
        rows=[dict(r) for r in self.rows]
        for r in rows:
            if r["slug"]=="galatasaray":r["last_match_date"]="2022-01-01"
        res=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:live(as_csv(rows)),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_SOURCE_OR_INTEGRITY_NOT_VERIFIED")
        rows=[dict(r) for r in self.rows]
        for r in rows:r["as_of"]="2026-11-05"
        res=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:live(as_csv(rows)),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_SOURCE_OR_INTEGRITY_NOT_VERIFIED")
    def test_duplicate_source_slug_refuses_mapping(self):
        rows=[dict(r) for r in self.rows]
        rows.append(dict(next(x for x in self.rows if x["slug"]=="liverpool")))
        scope=check_europe_scope("Galatasaray","Liverpool",IDX)
        res=reference_for_match(scope,fixture(),IDX,CO,REV,
            source_provider=lambda:live(as_csv(rows)),at_utc=FETCHED)
        self.assertEqual(res["status"],"ELO_IDENTITY_NOT_VERIFIED")
    def test_entrypoint_integrates_only_after_official_fixture(self):
        doc="""<html><body>
          <h1>2026/27 Champions League: All the league phase fixtures and results</h1>
          <p>Kick-offs are 21:00 unless stated; all times CET.</p>
          <h2>Matchday 4</h2><p>Wednesday 4 November 2026</p>
          <p>Galatasaray vs Liverpool</p>
          </body></html>"""
        calls=[]
        def source():
            calls.append("elo");return live(self.raw)
        got=requested_europe_match("UEFA_CL","Galatasaray","Liverpool",index=IDX,
             now=FETCHED,official_provider=lambda c:(doc,SOURCES[c]),enable_elo=True,
             elo_source_provider=source,elo_cohort=CO,elo_review=REV)
        self.assertTrue(got["fixture_verified"])
        self.assertEqual(calls,["elo"])
        self.assertEqual(got["europe_elo_reference"]["status"],"ELO_DESCRIPTIVE_REFERENCE_ATTACHED_NOT_MODEL_CALIBRATED",got)
        self.assertFalse(got["model_forecast_authorized"])
        self.assertFalse(got["ABC_approved"])
        self.assertIsNone(got["odds_EV"])
        self.assertFalse(got["pilot_recorded"])
    def test_official_fixture_failure_never_fetches_elo(self):
        got=requested_europe_match("UEFA_CL","Galatasaray","Liverpool",index=IDX,
             now=FETCHED,official_provider=lambda c:("<html>missing fixture</html>",SOURCES[c]),
             enable_elo=True,elo_source_provider=lambda:self.fail("elo fetched"),elo_cohort=CO,elo_review=REV)
        self.assertFalse(got["fixture_verified"])
        self.assertNotIn("europe_elo_reference",got)
    def test_older_season_using_nov2026_snapshot_not_allowed(self):
        sc=check_europe_scope("Arsenal","Barcelona",IDX)
        res=reference_for_match(sc,fixture("2025-11-04T20:00:00+00:00"),IDX,CO,REV,
            source_provider=lambda:self.fail("post kickoff fetched"),at_utc=FETCHED)
        self.assertEqual(res["status"],"MATCH_ALREADY_STARTED_SOURCE_NOT_FETCHED")
if __name__=="__main__": unittest.main()
