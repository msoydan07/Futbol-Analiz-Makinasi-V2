import copy, datetime as dt, unittest
from P0_HAFIZA_OTOMATIK_SONUC_V1 import source_pair, accepted_run, Pending, BRANCH, utc

KO=utc("2026-11-27T19:30:00Z")
DOC={"league":"GER1","home_id":"h","away_id":"a","kickoff_utc":KO.isoformat()}
FD=b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n27/11/2026,Team H,Team A,2,1,H\n"
ESPN={"events":[{"id":"sample-only","date":KO.isoformat(),"competitions":[
    {"status":{"type":{"name":"STATUS_FULL_TIME","completed":True}},
     "competitors":[{"homeAway":"home","team":{"displayName":"Team H"},"score":"2"},
                    {"homeAway":"away","team":{"displayName":"Team A"},"score":"1"}]}]}]}
def resolve(league,name):
    return {"Team H":"h","Team A":"a"}[name]

def run():
    return {"head_sha":"a"*40,"head_branch":BRANCH,"event":"push","conclusion":"success",
            "status":"completed","run_attempt":1,"created_at":"2026-11-27T10:00:00Z",
            "updated_at":"2026-11-27T10:01:00Z"}

class AutomaticResultTests(unittest.TestCase):
    def test_two_sources_agree(self):
        self.assertEqual(source_pair(DOC,FD,ESPN,resolve),((2,1),"sample-only"))
    def test_conflict_pending(self):
        e=copy.deepcopy(ESPN);e["events"][0]["competitions"][0]["competitors"][0]["score"]="3"
        with self.assertRaises(Pending):source_pair(DOC,FD,e,resolve)
    def test_wrong_date_pending(self):
        with self.assertRaises(Pending):source_pair(DOC,FD.replace(b"27/11",b"28/11"),ESPN,resolve)
    def test_wrong_kickoff_pending(self):
        e=copy.deepcopy(ESPN);e["events"][0]["date"]="2026-11-27T20:30:00Z"
        with self.assertRaises(Pending):source_pair(DOC,FD,e,resolve)
    def test_unfinished_pending(self):
        e=copy.deepcopy(ESPN);e["events"][0]["competitions"][0]["status"]["type"]["completed"]=False
        with self.assertRaises(Pending):source_pair(DOC,FD,e,resolve)
    def test_duplicate_pending(self):
        e=copy.deepcopy(ESPN);e["events"].append(copy.deepcopy(e["events"][0]))
        with self.assertRaises(Pending):source_pair(DOC,FD,e,resolve)
    def test_reversed_teams_pending(self):
        with self.assertRaises(Pending):source_pair(DOC,FD.replace(b"Team H,Team A",b"Team A,Team H"),ESPN,resolve)
    def test_preko_guard_acceptance(self):
        self.assertEqual(accepted_run([run()],"a"*40,KO),run())
    def test_postko_guard_rejected(self):
        r=run();r["updated_at"]=KO.isoformat()
        with self.assertRaises(Pending):accepted_run([r],"a"*40,KO)
    def test_rerun_rejected(self):
        r=run();r["run_attempt"]=2
        with self.assertRaises(Pending):accepted_run([r],"a"*40,KO)
    def test_wrong_branch_rejected(self):
        r=run();r["head_branch"]="main"
        with self.assertRaises(Pending):accepted_run([r],"a"*40,KO)
    def test_ambiguous_guard_rejected(self):
        with self.assertRaises(Pending):accepted_run([run(),run()],"a"*40,KO)

if __name__=="__main__":unittest.main()
