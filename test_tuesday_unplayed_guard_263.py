"""Nov 3 source refresh guard: distinguish FINAL results vs future blank scores.

New focused tests only. No 4,413-game backtests and no network calls.
"""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_fixture_candidates
import import_real_fixtures
from identity import Registry


def csv_payload(rows):
    fields=("Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR")
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=fields,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


class Response:
    def __init__(self,content):
        self.content=content
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self):
        return self.content


class DataRefreshGuard(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.rows=[
            {"Date":"01/11/2026","HomeTeam":"Dender","AwayTeam":"Cercle Brugge","FTHG":"2","FTAG":"1","FTR":"H"},
            {"Date":"08/11/2026","HomeTeam":"Dender","AwayTeam":"Cercle Brugge","FTHG":"","FTAG":"","FTR":""},
        ]

    def test_forthcoming_scores_are_never_candidate_for_completed_history(self):
        data=csv_payload(self.rows)
        with patch.object(audit_fixture_candidates,"OUT",self.root),\
             patch.object(audit_fixture_candidates,"LEAGUES",{"BEL1":"B1"}),\
             patch.object(audit_fixture_candidates,"SEASONS",{"2026-2027":"2627"}),\
             patch.object(audit_fixture_candidates.urllib.request,"urlopen",
                          return_value=Response(data)):
            audit_fixture_candidates.main()
        entries=list(csv.DictReader((self.root/"fixture_candidates.csv").open()))
        self.assertEqual([x["status"] for x in entries],
                         ["CANDIDATE_ONLY","UNPLAYED_SOURCE_ROW"])
        self.assertEqual(entries[0]["source_row"],"2")
        self.assertEqual(entries[1]["source_row"],"3")
        self.assertEqual(entries[1]["candidate_key"],"")

    def test_importer_skips_future_without_creating_fixture(self):
        reg=Registry(self.root/"team_registry.json")
        reg.register_team("dender","Dender")
        reg.register_team("cercle-brugge","Cercle Brugge")
        reg.save()
        entries=[
            {"season":"2026-2027","league":"BEL1","source_row":"2","date":"01/11/2026",
             "home":"Dender","away":"Cercle Brugge","candidate_key":"good","status":"CANDIDATE_ONLY"},
            {"season":"2026-2027","league":"BEL1","source_row":"3","date":"08/11/2026",
             "home":"Dender","away":"Cercle Brugge","candidate_key":"","status":"UNPLAYED_SOURCE_ROW"}]
        with (self.root/"fixture_candidates.csv").open("w",newline="") as out:
            w=csv.DictWriter(out,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
        with (self.root/"fixture_source_audit.csv").open("w",newline="") as out:
            w=csv.DictWriter(out,fieldnames=["season","league","status"])
            w.writeheader();w.writerows({"season":"2026-2027","league":f"L{j}","status":"OK"} for j in range(20))
        with patch.object(import_real_fixtures,"ROOT",self.root):
            import_real_fixtures.main()
        register=json.loads((self.root/"match_registry.json").read_text())
        self.assertEqual(len(register["fixtures"]),1)
        summary=json.loads((self.root/"fixture_import_report.json").read_text())
        self.assertEqual(summary["skipped_unplayed_source_rows"],1)
        self.assertEqual(summary["error_count"],0)

    def test_invalid_half_final_result_is_not_silent_fixture(self):
        malformed=[dict(self.rows[1],FTHG="1",FTAG="",FTR="")]
        data=csv_payload(malformed)
        with patch.object(audit_fixture_candidates,"OUT",self.root),\
             patch.object(audit_fixture_candidates,"LEAGUES",{"BEL1":"B1"}),\
             patch.object(audit_fixture_candidates,"SEASONS",{"2026-2027":"2627"}),\
             patch.object(audit_fixture_candidates.urllib.request,"urlopen",return_value=Response(data)):
            audit_fixture_candidates.main()
        row=list(csv.DictReader((self.root/"fixture_candidates.csv").open()))[0]
        self.assertEqual(row["status"],"INVALID_RESULT_INCOMPLETE_RESULT")


if __name__=="__main__":
    unittest.main()
