"""One offline acceptance for 17 source-reviewed 3-5 Nov 2026 UEFA fixtures.
The review data comes from ChatGPT inspecting the official 2026/27 CL + EL
articles and 17 official match-page links on Nov 3, NOT runner refetch.
"""
from __future__ import annotations
import copy
import json
import sys
import unittest
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from uefa_web_evidence_handoff_263 import requested_from_web_evidence
from uefa_requested_match_entry_263 import index_with_reviewed_uefa_names
from uefa_ten_league_scope_gate_263 import check_europe_scope

INDEX=Path("experiments/263/evidence/identity_index_263.json")
COHORT=Path("experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json")
FIXTURES=Path("experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json")
EVIDENCE=Path("experiments/263/evidence/uefa_web_2026_11_03_17_matches_review_only.json")
OUTPUT=Path("data/europe_staged_263/2026_11_03_05_fixture_scope_acceptance/assisted_17_scope_gate_report.json")
NOW=datetime.fromisoformat("2026-11-03T06:10:00+00:00")

def audit_offline(evidence_override=None):
    index=json.loads(INDEX.read_text(encoding="utf-8"))
    before=copy.deepcopy(index)
    cohort=json.loads(COHORT.read_text(encoding="utf-8"))
    raw=json.loads(FIXTURES.read_text(encoding="utf-8"))
    evidence=evidence_override if evidence_override is not None else json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if not (len(cohort["eligible_team_ids"])==167 and
            len(raw["verified_fixtures"])==17 and
            len(raw["unselected_fixtures"])==19 and
            len(evidence["fixtures"])==17):
        raise ValueError("REVIEW_MATCH_OR_COHORT_COUNTS_INVALID")
    active=set(cohort["eligible_team_ids"])
    scoped_index=index_with_reviewed_uefa_names(index)
    if index!=before:raise ValueError("BASE_CANONICAL_REGISTRY_MUTATED")
    details=[]
    for rec in raw["verified_fixtures"]:
        cup=rec["competition"];home=rec["home_uefa"];away=rec["away_uefa"]
        expected=rec["kickoff_utc"]
        gate=check_europe_scope(home,away,scoped_index)
        if not gate["allow_further_research"]:
            raise ValueError("MATCH_NOT_IN_TEN_LEAGUE_GATE:"+home+" / "+away)
        if (gate["home"]["canonical_team_id"] not in active or
            gate["away"]["canonical_team_id"] not in active):
            raise ValueError("MATCH_NOT_IN_167_ELO_COHORT:"+home+" / "+away)
        got=requested_from_web_evidence(cup,home,away,index=index,now=NOW,evidence=evidence)
        if (got["status"]!="ASSISTED_WEB_OFFICIAL_ARTICLE_FIXTURE_REFERENCE_ACCEPTED" or
            got["fixture"]["kickoff_utc"]!=expected or
            got["fixture"]["match_date"]!=rec["date"] or
            got["fixture"]["matchday"]!=4 or
            got["fixture"]["competition"]!=cup):
            raise ValueError("ASSISTED_FIXTURE_OR_KICKOFF_NOT_ACCEPTED:"+home+" / "+away+" "+str(got))
        if (got["live_automated_UEFA_verification"] is not False or
            got["official_UEFA_page_fetched_by_runner"] is not False or
            got["model_forecast_authorized"] is not False or
            got["pilot_recorded"] is not False):
            raise ValueError("REVIEW_SOURCE_MISREPRESENTED_AS_LIVE_MODEL")
        details.append({"date":rec["date"],"competition":cup,
                        "uefa_match_id":rec["uefa_match_id"],
                        "home":home,"away":away,
                        "home_id":gate["home"]["canonical_team_id"],
                        "away_id":gate["away"]["canonical_team_id"],
                        "kickoff_utc":expected,
                        "turkey_time":rec["kickoff_turkey"],
                        "official_match_url":rec["official_match_url"],
                        "status":"ASSISTED_WEB_OFFICIAL_ARTICLE_FIXTURE_REFERENCE_ACCEPTED"})
    for rec in raw["unselected_fixtures"]:
        if (rec["home_scope"]["canonical_team_id"] in active and
            rec["away_scope"]["canonical_team_id"] in active):
            raise ValueError("UNSELECTED_FIXTURE_BOTH_TEAMS_IN_167")
    days=Counter(r["date"] for r in details)
    cups=Counter(r["competition"] for r in details)
    clubs={id for r in details for id in (r["home_id"],r["away_id"])}
    if (days!=Counter({"2026-11-03":6,"2026-11-04":6,"2026-11-05":5}) or
        cups!=Counter({"UEFA_CL":12,"UEFA_EL":5}) or len(clubs)!=34):
        raise ValueError("EXPECTED_DISTRIBUTIONS_CHANGED")
    return {
        "schema":"263_NOV3_5_OFFICIAL_WEB_ASSISTED_FIXTURE_COHORT_ACCEPTANCE_V1",
        "status":"17_OFFICIAL_WEB_ASSISTED_FIXTURES_AND_CANONICAL_SCOPE_ACCEPTED",
        "source_checked_on_istanbul":"2026-11-03",
        "source_method":"ASSISTANT_WEB_OFFICIAL_ARTICLE_REFERENCE",
        "source_urls":{c:v["source_url"] for c,v in evidence["sources"].items()},
        "original_total_official_fixtures":36,
        "candidate_total":17,
        "unselected_total":19,
        "by_day":dict(sorted(days.items())),
        "by_competition":dict(sorted(cups.items())),
        "distinct_canonical_clubs":len(clubs),
        "source_date_freshness_max_days":1,
        "on_2026_11_05_must_recheck_web_freshness":True,
        "club_uefa_numeric_ids_independently_verified":False,
        "github_runner_live_uefa_access_verified":False,
        "github_runner_previous_timeout_known":True,
        "web_source_reviewed_with_real_uefa_article_and_17_match_links":True,
        "team_registries_main_and_domestic_10_leagues_changed":False,
        "mathematical_prediction_produced":False,
        "pilot_or_immutable_prediction_recorded":False,
        "elo_weight_for_poisson_approved":False,
        "results":details
    }

class FixtureGate(unittest.TestCase):
    def test_all_17_assisted_sources_and_ten_league_gate(self):
        result=audit_offline()
        self.assertEqual(result["candidate_total"],17)
        self.assertEqual(result["distinct_canonical_clubs"],34)
    def test_three_uefa_names_have_distinct_federation_verified_ids_without_mutation(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        old=copy.deepcopy(index)
        reviewed=index_with_reviewed_uefa_names(index)
        for source_name,name in (
            ("Bayern München","FC Bayern München"),
            ("Leipzig","RB Leipzig"),
            ("Union SG","Royale Union Saint-Gilloise")):
            from uefa_ten_league_scope_gate_263 import norm
            self.assertEqual(index["teams"][reviewed["aliases"][norm(source_name)]]["name"],name)
        self.assertEqual(index,old)
    def test_celtic_out_of_index_never_reads_fixture_evidence(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        calls=[]
        got=requested_from_web_evidence(
            "UEFA_EL","Celtic","Beşiktaş",index=index,now=NOW,
            evidence_loader=lambda:calls.append("fileopened"))
        self.assertEqual(got["status"],"ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED")
        self.assertFalse(calls)
    def test_stale_web_reference_is_not_accepted(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        now=datetime.fromisoformat("2026-11-05T06:00:00+00:00")
        r=requested_from_web_evidence("UEFA_EL","Celta","Union SG",
            index=index,now=now,evidence=evidence)
        self.assertEqual(r["status"],"ASSISTED_OFFICIAL_WEB_EVIDENCE_NOT_ACCEPTED")
        self.assertEqual(r["evidence_rejection_reason"],"WEB_EVIDENCE_STALE_OR_FROM_FUTURE")
    def test_wrong_time_fails_to_match_curated_official_info(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        rows=copy.deepcopy(evidence)
        for row in rows["fixtures"]:
            if row["fixture_line"].startswith("Galatasaray vs Stuttgart"):
                row["fixture_line"]="Galatasaray vs Stuttgart"
        with self.assertRaisesRegex(ValueError,"ASSISTED_FIXTURE_OR_KICKOFF_NOT_ACCEPTED"):
            audit_offline(rows)

def main():
    report=audit_offline()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("UEFA_NOV3_5_WEB_ASSISTED_STAGE3="+json.dumps({
        "status":report["status"],"matches":report["candidate_total"],
        "days":report["by_day"],"cup_counts":report["by_competition"],
        "live_runner_verification":False,"no_prediction_recorded":True},
        ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    if "--write-report" in sys.argv:main()
    else:unittest.main()
