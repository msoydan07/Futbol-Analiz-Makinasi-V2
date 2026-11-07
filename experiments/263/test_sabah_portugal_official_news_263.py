"""One nine-match official Portugal schedule acceptance, zero live odds."""
import unittest
from datetime import datetime,timezone
from sabah_portugal_official_news_263 import parse_news,SOURCE_URL,PARSER,START
from official_page_lookup_263 import SOURCES,official_page_lookup
from sabah_official_fixture_gateway_263 import OfficialFixtureGateway

DAY=[
("Sexta-feira, 6 de novembro",[
 "FC Famalicão - FC Arouca, 20h45 – SportTV"]),
("Sábado, 7 de novembro",[
 "CD Nacional – Académico, 15h30 - SportTV",
 "FC Alverca - Casa Pia AC, 18h00 - SportTV",
 "Sporting CP - Moreirense FC, 20h30 – SportTV"]),
("Domingo, 8 de novembro",[
 "Estoril Praia - Marítimo M, 15h30 - SportTV",
 "Santa Clara - Gil Vicente FC, 15h30 - SportTV",
 "Vitória SC - FC Porto, 18h00 - SportTV",
 "Estrela Amadora - SL Benfica, 20h30 - SportTV",
 "Rio Ave FC - SC Braga, 20h30 - SportTV"])]
def synthetic():
    # Models raw serialized escaped <p> as observed in 7 Nov
    # live official Liga Portugal HTML artifact.
    parts=[r"\u003Cp>"+START+r"\u003C/p>"]
    for d,ms in DAY:
        parts.append(r"\u003Cp\u003Cstrong>"+d+r"\u003C/strong>\u003C/p>")
        parts.extend(r"\u003Cp>"+m+r"\u003C/p>" for m in ms)
    return "<html><title>Media Kits - Jornada 11 da Liga Portugal Betclic</title></html>"+ "".join(parts)
class PortugalNews(unittest.TestCase):
    def test_nine_official_times_timezone_and_3_plus_5(self):
        rows=parse_news(synthetic())
        self.assertEqual(len(rows),9)
        self.assertEqual(sum(r["match_date"]=="2026-11-07" for r in rows),3)
        self.assertEqual(sum(r["match_date"]=="2026-11-08" for r in rows),5)
        self.assertEqual(rows[3]["home"],"Sporting CP")
        self.assertEqual(rows[3]["away"],"Moreirense FC")
        self.assertEqual(rows[3]["kickoff_utc"],"2026-11-07T20:30:00+00:00")
        self.assertEqual(rows[-1]["kickoff_utc"],"2026-11-08T20:30:00+00:00")
        self.assertTrue(all(r["format"]==PARSER for r in rows))
    def test_missing_one_row_fails_closed(self):
        doc=synthetic().replace(r"\u003Cp>Rio Ave FC - SC Braga, 20h30 - SportTV\u003C/p>","")
        self.assertEqual(parse_news(doc),[])
    def test_unrelated_editorial_or_unverified_year_blocked(self):
        self.assertEqual(parse_news(synthetic().replace("Media Kits - Jornada 11","Media Kits - Jornada 12")),[])
        self.assertEqual(parse_news(synthetic().replace("Domingo, 8 de novembro","Domingo, 9 de novembro")),[])
    def test_ambiguous_duplicate_blocked(self):
        dup=synthetic().replace("Santa Clara - Gil Vicente FC, 15h30",
                                "Estoril Praia - Marítimo M, 15h30")
        self.assertEqual(parse_news(dup),[])
    def test_live_fixture_lookup_uses_selected_parser(self):
        calls=[]
        def fetch(url,league):
            calls.append(url)
            if url==SOURCE_URL:return url,synthetic()
            if url==SOURCES["POR1"][0]:return url,"<html>Empty JS-only official calendar</html>"
            raise AssertionError("UNEXPECTED_SOURCE")
        def gate(league,home,away,lookup_override=None):
            r=lookup_override(home,away)
            self.assertEqual(r["source_parser"],PARSER)
            self.assertEqual(r["status"],"VERIFIED_OFFICIAL_FIXTURE")
            return {"status":"VERIFIED","league":league,"home":home,"away":away}
        gw=OfficialFixtureGateway(fetcher=fetch,gate_runner=gate,
            resolve_id=lambda lg,name:name.casefold(),
            clock=lambda:datetime(2026,11,7,12,0,tzinfo=timezone.utc))
        result=gw.lookup("POR1","Sporting CP","Moreirense FC")
        self.assertEqual(result["status"],"VERIFIED")
        self.assertEqual(calls.count(SOURCE_URL),1)
        self.assertEqual(len(gw._get("POR1")["events"]),9)
        self.assertEqual(calls.count(SOURCE_URL),1)
        self.assertEqual(gw.coverage()["POR1"]["parsed_events"],9)
    def test_fallback_fail_closed_in_2027(self):
        calls=[]
        def fetch(url,league):
            calls.append(url)
            return url,"<html>Calendar JavaScript only</html>"
        gw=OfficialFixtureGateway(fetcher=fetch,
            resolve_id=lambda lg,n:n.casefold(),
            clock=lambda:datetime(2027,11,7,12,tzinfo=timezone.utc))
        x=gw._get("POR1")
        self.assertEqual(x["events"],[])
        self.assertNotIn(SOURCE_URL,calls)
    def test_news_source_not_other_domain(self):
        r=official_page_lookup("POR1","Sporting CP","Moreirense FC",
             now=datetime(2026,11,7,12,tzinfo=timezone.utc),
             source_url="https://other.test/fake",
             html=synthetic(),same_team=lambda a,b:a==b,parser=PARSER)
        self.assertEqual(r["status"],"REJECTED")
if __name__=="__main__":unittest.main()
