"""Nov-3 source audit: 20 sources containing completed AND unplayed fixtures.

Offline mocks; never open network and never start prediction registration.
"""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_historical_results as build
from identity import Registry
from collect_team_candidates import LEAGUES, SEASONS


class SourceResponse:
    def __init__(self, data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return self.data


def source_csv(final=True,invalid=False):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=("Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"),
                          lineterminator="\n")
    writer.writeheader()
    writer.writerow({"Date":"01/10/2025","HomeTeam":"Team A","AwayTeam":"Team B",
                     "FTHG":"2","FTAG":"1","FTR":"H" if not invalid else "A"})
    if not final:
        writer.writerow({"Date":"08/11/2026","HomeTeam":"Team A","AwayTeam":"Team B",
                         "FTHG":"","FTAG":"","FTR":""})
    return out.getvalue().encode()


class FrozenSourceResultsGuard(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        reg=Registry(self.root/"team_registry.json")
        ah=reg.register_team("team-a","Team A")
        aw=reg.register_team("team-b","Team B")
        candidates=[]
        source_audits=[]
        for season in SEASONS:
            for league in LEAGUES:
                # Distinct season+league identity despite shared placeholder teams.
                reg.register_dated_fixture(league,season,ah,aw,"2025-10-01")
                source_audits.append({"season":season,"league":league,"status":"OK",
                                      "rows":"2"})
                candidates.extend([
                    {"season":season,"league":league,"source_row":"2","home":"Team A",
                     "away":"Team B","date":"01/10/2025","status":"CANDIDATE_ONLY"},
                    {"season":season,"league":league,"source_row":"3","home":"Team A",
                     "away":"Team B","date":"08/11/2026","status":"UNPLAYED_SOURCE_ROW"}
                ])
        reg.path=self.root/"match_registry.json";reg.save()
        self.write_csv("fixture_candidates.csv",candidates)
        self.write_csv("fixture_source_audit.csv",source_audits)

    def write_csv(self,name,records):
        with (self.root/name).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=records[0])
            writer.writeheader();writer.writerows(records)

    def call(self,invalid=False):
        data=source_csv(final=False,invalid=invalid)
        with patch.object(build,"ROOT",self.root),patch.object(build.urllib.request,"urlopen",
                          side_effect=lambda request,timeout:SourceResponse(data)):
            return build.build()

    def test_twenty_sources_only_completed_scores_counted(self):
        self.call()
        audit=json.loads((self.root/"historical_results_audit.json").read_text())
        self.assertTrue(audit["accepted"])
        self.assertEqual(audit["sources"],20)
        self.assertEqual(audit["candidate_source_rows_total"],40)
        self.assertEqual(audit["expected_rows"],20)
        self.assertEqual(audit["linked"],20)
        self.assertEqual(audit["skipped_unplayed_source_rows"],20)
        with (self.root/"historical_results.csv").open(newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),20)
        self.assertEqual({r["result"] for r in rows},{"H"})
        self.assertFalse((self.root/"forward_quad_263").exists())

    def test_inconsistent_result_fails_closed_no_history(self):
        with self.assertRaisesRegex(SystemExit,"rejected"):
            self.call(invalid=True)
        audit=json.loads((self.root/"historical_results_audit.json").read_text())
        self.assertFalse(audit["accepted"])
        self.assertTrue(audit["errors"])
        self.assertFalse((self.root/"historical_results.csv").exists())


if __name__=="__main__":
    unittest.main()
