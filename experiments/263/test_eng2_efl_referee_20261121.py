"""Referee-source strict tests: eleven explicit Championship fixtures only."""
import unittest
from datetime import datetime,timezone
from sabah_eng2_referee_nov21_263 import parse_efl_referee_j16,SOURCE
from official_page_lookup_263 import official_page_lookup,SOURCES

PAIRS=[
("Millwall","Queens Park Rangers","12:30pm"),
("Norwich City","Cardiff City","12:30pm"),
("Southampton","Derby County","12:30pm"),
("Bolton Wanderers","Portsmouth","3:00pm"),
("Lincoln City","Wrexham","3:00pm"),
("Middlesbrough","Bristol City","3:00pm"),
("Sheffield United","Watford","3:00pm"),
("Stoke City","Birmingham City","3:00pm"),
("Swansea City","West Bromwich Albion","3:00pm"),
("West Ham United","Preston North End","3:00pm"),
("Wolverhampton Wanderers","Charlton Athletic","3:00pm")
]
def mocked_article(pairs=PAIRS):
    cards="\\n".join(f"<h5>{h} v {a} ({t})</h5>\\n<p>Referee</p>" for h,a,t in pairs)
    return ('<title>Referee Appointments: 20 - 26 November</title> 18 Nov 2026 '
        '<script>content:"<h3>Sky Bet Championship</h3>\\n'
        '<h4>Saturday 21 November</h4>\\n'+cards+'\\n'
        '<h4>Sunday 22 November</h4>\\n'
        '<h3>Sky Bet League One</h3>"</script>')
class EflRefereeAcceptance(unittest.TestCase):
    def test_exact_eleven_utc_and_names(self):
        a=parse_efl_referee_j16(mocked_article())
        self.assertEqual(len(a),11)
        self.assertEqual({(r["home"],r["away"],r["kickoff_utc"]) for r in a},
          {(h,a, "2026-11-21T12:30:00+00:00" if t=="12:30pm" else "2026-11-21T15:00:00+00:00") for h,a,t in PAIRS})
    def test_incomplete_and_wrong_week_stay_unverified(self):
        self.assertFalse(parse_efl_referee_j16(mocked_article(PAIRS[:-1])))
        self.assertFalse(parse_efl_referee_j16(mocked_article().replace("Saturday 21 November","Saturday 28 November")))
        self.assertFalse(parse_efl_referee_j16(mocked_article().replace("Sky Bet Championship","Sky Bet League One")))
    def test_reversed_is_blocked(self):
        a=official_page_lookup("ENG2","Millwall","Queens Park Rangers",
            now=datetime(2026,11,21,9,tzinfo=timezone.utc),
            source_url=SOURCE,html=mocked_article(),
            parser="efl_referee_j16_20261121",same_team=lambda x,y:x==y)
        self.assertEqual(a["status"],"VERIFIED_OFFICIAL_FIXTURE")
        b=official_page_lookup("ENG2","Queens Park Rangers","Millwall",
            now=datetime(2026,11,21,9,tzinfo=timezone.utc),
            source_url=SOURCE,html=mocked_article(),
            parser="efl_referee_j16_20261121",same_team=lambda x,y:x==y)
        self.assertNotEqual(b["status"],"VERIFIED_OFFICIAL_FIXTURE")
if __name__=="__main__":unittest.main()
