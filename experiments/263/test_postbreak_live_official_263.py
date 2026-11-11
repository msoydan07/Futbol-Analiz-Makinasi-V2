"""Offline safety regression only: mocked official HTML, no bookmaker calls."""
import unittest
from datetime import datetime,timezone
from iddaa_pdf_live_official_263 import lookup,CURRENT_PAGES
from postbreak_freshness_gate_263 import freshness_gate,EXCEPTIONS
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label

T=datetime(2026,11,21,10,0,tzinfo=timezone.utc)
PL_HTML="""<html><body>
<h1>Fixture amendments for Premier League matches in November</h1>
<p>November 2026 schedule</p>
<p>All fixtures are GMT and are 15:00 kick-offs unless otherwise stated</p>
<p>Saturday 21 November</p><p>12:30 Man City v Fulham (TNT Sports)</p>
<p>Aston Villa v Sunderland</p>
</body></html>"""
EFL_HTML="""<html><body><h1>Sky Sports Championship selections</h1>
<table><tr><td>Championship</td><td>21-Nov-26</td><td>Saturday</td>
<td>12:30</td><td>Millwall</td><td>V</td><td>Queens Park Rangers</td><td>Sky Sports</td></tr></table></body></html>"""

class RealSourceAndBreakGate(unittest.TestCase):
    def test_current_official_sources_exclude_stale_week11_articles(self):
        self.assertIn("/4725574",CURRENT_PAGES["ENG1"][0])
        for lg in ("ESP1","ITA1","FRA1"):
            self.assertNotIn("j11",CURRENT_PAGES[lg][0].lower())
            self.assertNotIn("arbitrali",CURRENT_PAGES[lg][0].lower())

    def test_november_official_premier_kickoff_and_no_wrong_team_guess(self):
        url=CURRENT_PAGES["ENG1"][0]
        calls=[]
        def fetch(page):
            calls.append(page)
            return page,PL_HTML
        found=lookup("ENG1","Manchester City","Fulham",now=T,fetcher=fetch)
        self.assertEqual(found["status"],"VERIFIED_OFFICIAL_FIXTURE",found)
        self.assertEqual(found["kickoff_utc"],"2026-11-21T12:30:00+00:00")
        self.assertEqual(calls,[url])
        reversed_=lookup("ENG1","Fulham","Manchester City",now=T,fetcher=fetch)
        self.assertEqual(reversed_["status"],"NOT_VERIFIED")

    def test_efl_tv_partial_coverage_and_wrong_club_block(self):
        found=lookup("ENG2","Millwall","Queens Park Rangers",now=T,
                     fetcher=lambda url:(url,EFL_HTML))
        self.assertEqual(found["status"],"VERIFIED_OFFICIAL_FIXTURE",found)
        self.assertEqual(found["coverage"],"OFFICIAL_PARTIAL_TELEVISED_ONLY")
        wrong=lookup("ENG2","Millwall","Preston North End",now=T,
                     fetcher=lambda url:(url,EFL_HTML))
        self.assertEqual(wrong["status"],"NOT_VERIFIED")

    def test_javascript_no_timed_events_never_confirms_a_fixture(self):
        for lg,home,away in (("ITA1","Inter","Milan"),
                             ("ESP1","Real Madrid","Barcelona"),
                             ("FRA1","PSG","Marseille")):
            result=lookup(lg,home,away,now=T,fetcher=lambda u:(u,"<html>Loading...</html>"))
            self.assertNotEqual(result.get("status"),"VERIFIED_OFFICIAL_FIXTURE")

    def test_break_all_ten_scoped_leagues_and_sources(self):
        self.assertEqual(set(EXCEPTIONS),set(("ENG1","ENG2","GER1","ESP1","ITA1",
                                           "FRA1","NED1","TUR1","POR1","BEL1")))
        for lg,cfg in EXCEPTIONS.items():
            date=cfg["official_scope"].split("/")[0]
            at=datetime.fromisoformat(date+"T10:00:00+00:00")
            ko=datetime.fromisoformat(date+"T12:30:00+00:00")
            gate={"status":"VERIFIED","source_url":cfg["source"],
                  "retrieved_at_utc":at.isoformat(),"kickoff_utc":ko.isoformat()}
            result=freshness_gate(league=lg,latest="2026-11-07",
                    match_date=date,gate=gate,now=at)
            self.assertEqual(result["status"],"REVIEWED_FIRST_POST_BREAK_SCHEDULE_ONLY",
                    (lg,result))
            for bad in ("https://unofficial.com","https://www.tff.org/"):
                changed={**gate,"source_url":bad}
                self.assertTrue(freshness_gate(league=lg,latest="2026-11-07",
                    match_date=date,gate=changed,now=at)["status"].startswith("BLOCKED"))
        self.assertTrue(freshness_gate(league="TUR1",latest="2026-11-08",
                match_date="2026-11-21",gate={},now=T)["status"].startswith("BLOCKED"))

    def test_break_never_extends_to_later_round_or_missing_recent_scores(self):
        gate={"status":"VERIFIED","source_url":EXCEPTIONS["ENG1"]["source"],
              "retrieved_at_utc":T.isoformat(),"kickoff_utc":"2026-11-21T12:30:00+00:00"}
        for latest,day in (("2026-11-05","2026-11-21"),
                           ("2026-11-08","2026-11-29"),
                           ("2026-11-08","2026-12-01")):
            self.assertTrue(freshness_gate(league="ENG1",latest=latest,
                match_date=day,gate=gate,now=T)["status"].startswith("BLOCKED"))
        self.assertEqual(freshness_gate(league="TUR1",latest="2026-11-14",
            match_date="2026-11-21",gate={},now=T)["status"],"NORMAL_TEN_DAY_LIMIT")


    def test_actual_knvb_short_nec_identity_is_exact_canonical(self):
        idx,_,_=index_registry()
        self.assertEqual(resolve_label("NED1","N.E.C.",idx)["status"],"MAPPED")
        self.assertEqual(resolve_label("NED1","N.E.C.",idx)["team_id"],
                         resolve_label("NED1","N.E.C. Nijmegen",idx)["team_id"])

    def test_official_tff_nov12_round_uses_only_exact_cells_and_clock(self):
        from postbreak_official_parsers_263 import parse_tff_round12
        names=[
         ("21.11.2026 13:30","GENÇLERBİRLİĞİ","GAZİANTEP FUTBOL KULÜBÜ A.Ş."),
         ("21.11.2026 16:00","AMED SPORTİF FAALİYETLER","ÇAYKUR RİZESPOR A.Ş."),
         ("21.11.2026 16:00","GALATASARAY A.Ş.","SAMSUNSPOR A.Ş."),
         ("21.11.2026 19:00","KOCAELİSPOR","FENERBAHÇE A.Ş."),
         ("22.11.2026 13:30","ERZURUMSPOR FK","GÖZTEPE A.Ş."),
         ("22.11.2026 16:00","KASIMPAŞA A.Ş.","CORENDON ALANYASPOR"),
         ("22.11.2026 16:00","TÜMOSAN KONYASPOR","BEŞİKTAŞ A.Ş."),
         ("22.11.2026 19:00","TRABZONSPOR A.Ş.","EYÜPSPOR"),
         ("23.11.2026 20:00","İSTANBUL BAŞAKŞEHİR FK","ARCA ÇORUM FK")]
        prefix="<h1>Trendyol Süper Lig 2026-2027 Sezonu Fikstürü</h1><p>12.Hafta</p>"
        def build(rows):
            return "<html>"+prefix+"<table>"+"".join(
                "<tr><td>"+dt+"</td><td>"+h+"</td><td>-</td><td>"+a+"</td><td>Detaylar</td></tr>"
                for dt,h,a in rows)+"</table></html>"
        source=build(names)
        self.assertEqual(len(parse_tff_round12(source)),9)
        result=lookup("TUR1","GALATASARAY A.Ş.","SAMSUNSPOR A.Ş.",
            now=datetime(2026,11,21,11,0,tzinfo=timezone.utc),
            fetcher=lambda u:(u,source))
        self.assertEqual(result["status"],"VERIFIED_OFFICIAL_FIXTURE",result)
        self.assertEqual(result["kickoff_utc"],"2026-11-21T13:00:00+00:00")
        self.assertEqual(parse_tff_round12(build(names[:-1])),[])
        self.assertEqual(lookup("TUR1","SAMSUNSPOR A.Ş.","GALATASARAY A.Ş.",
            now=datetime(2026,11,21,11,0,tzinfo=timezone.utc),
            fetcher=lambda u:(u,source))["status"],"NOT_VERIFIED")

    def test_french_official_11th_round_full_fixture_context(self):
        from postbreak_official_parsers_263 import parse_ligue1_round11
        pairs=[
            ("Vendredi 20 novembre 2026 à 20h45 sur Ligue 1+",
             ("ESTAC Troyes – Havre AC",)),
            ("Samedi 21 novembre 2026 à 17h15 sur Ligue 1+",
             ("OGC Nice – Paris Saint-Germain",)),
            ("Samedi 21 novembre 2026 à 20h45 sur Ligue 1+",
             ("LOSC – Olympique Lyonnais","RC Lens – Toulouse FC",
              "AS Monaco – AJ Auxerre","RC Strasbourg Alsace – Stade Brestois 29")),
            ("Dimanche 22 novembre 2026 à 15h00 sur Ligue 1+",
             ("Paris FC – Angers SCO",)),
            ("Dimanche 22 novembre 2026 à 17h15 sur Ligue 1+",
             ("FC Lorient – Stade Rennais FC",)),
            ("Dimanche 22 novembre 2026 à 20h45 sur Ligue 1+",
             ("Olympique de Marseille – Le Mans FC",))]
        def page(groups):
            return "<html><h1>Programmations TV : J10 et J11</h1><h2>11e JOURNÉE DE LIGUE 1 McDONALD’S</h2>"+ "".join(
                "<p>"+heading+"</p>"+"".join("<p>"+s+"</p>" for s in games)
                for heading,games in groups)+"</html>"
        document=page(pairs)
        self.assertEqual(len(parse_ligue1_round11(document)),9)
        sample=lookup("FRA1","OGC Nice","Paris Saint-Germain",
            now=datetime(2026,11,20,12,0,tzinfo=timezone.utc),
            fetcher=lambda u:(u,document))
        self.assertEqual(sample["status"],"VERIFIED_OFFICIAL_FIXTURE",sample)
        self.assertEqual(parse_ligue1_round11(page(pairs[:-1])),[])

    def test_portugal_nov27_official_nine_game_context_never_partial(self):
        from postbreak_official_parsers_263 import parse_portugal_round12
        data=[
        ("Sexta-feira, 27 de novembro",("Marítimo M. - CD Nacional, 20h15 - SportTV",)),
        ("Sábado, 28 de novembro",("FC Arouca - Rio Ave FC, 15h30 - SportTV",
             "Moreirense FC - Santa Clara, 15h30 - TVI",
             "Académico - FC Alverca, 18h00 - SportTV",
             "Vitória SC - Estrela Amadora, 20h30 - SportTV")),
        ("Domingo, 29 de novembro",("Gil Vicente FC - Estoril Praia, 18h00 - SportTV",
             "FC Porto - Sporting CP, 20h30 - SportTV")),
        ("Segunda-feira, 30 de novembro",("Casa Pia AC - SC Braga, 20h15 - SportTV",
             "SL Benfica - FC Famalicão, 20h15 - BTV"))]
        def page(groups):
            return "<h1>Horários definidos até à 12.ª jornada</h1><p>Jornada 12</p>"+ "".join(
                "<p>"+heading+"</p>"+"".join("<p>"+s+"</p>" for s in games)
                for heading,games in groups)+"</html>"
        html=page(data)
        self.assertEqual(len(parse_portugal_round12(html)),9)
        self.assertEqual(parse_portugal_round12(page(data[:-1])),[])
        r=lookup("POR1","FC Porto","Sporting CP",
            now=datetime(2026,11,29,16,0,tzinfo=timezone.utc),
            fetcher=lambda u:(u,html))
        self.assertEqual(r["status"],"VERIFIED_OFFICIAL_FIXTURE",r)


    def test_efl_serialized_official_tv_table_is_parsed_but_only_partial(self):
        from sabah_eng2_official_tv_263 import parse_efl_tv
        tr='<tr><td>Championship</td><td>21-Nov-26</td><td>Saturday</td>'+
           '<td>12:30</td><td>Millwall</td><td>V</td><td>Queens Park Rangers</td>'+
           '<td>Sky Sports Football</td></tr>'
        page='<html><h1>Sky Sports Championship</h1><script>const body="<table>'+tr+'</table>";</script></html>'
        rows=parse_efl_tv(page)
        self.assertEqual(len(rows),1,rows)
        self.assertEqual(rows[0]["home"],"Millwall")
        self.assertEqual(rows[0]["kickoff_utc"],"2026-11-21T12:30:00+00:00")
        wrong=page.replace('<td>Championship</td>','<td>League One</td>')
        self.assertEqual(parse_efl_tv(wrong),[])

    def test_portugal_nuxt_escaped_article_is_decoded_inside_strict_round12(self):
        from postbreak_official_parsers_263 import parse_portugal_round12
        paragraphs=[
          'Jornada 12',
          'Sexta-feira, 27 de novembro',
          'Marítimo M. - CD Nacional, 20h15 - SportTV',
          'Sábado, 28 de novembro',
          'FC Arouca - Rio Ave FC, 15h30 - SportTV',
          'Moreirense FC - Santa Clara, 15h30 - TVI',
          'Académico - FC Alverca, 18h00 - SportTV',
          'Vitória SC - Estrela Amadora, 20h30 - SportTV',
          'Domingo, 29 de novembro',
          'Gil Vicente FC - Estoril Praia, 18h00 - SportTV',
          'FC Porto - Sporting CP, 20h30 - SportTV',
          'Segunda-feira, 30 de novembro',
          'Casa Pia AC - SC Braga, 20h15 - SportTV',
          'SL Benfica - FC Famalicão, 20h15 - BTV']
        serialized=''.join(r'\u003Cp>'+s+r'\u003C/p>' for s in paragraphs)
        page='<html><title>Horários definidos até à 12.ª jornada</title><script>window.__NUXT__="'+serialized+'";</script></html>'
        events=parse_portugal_round12(page)
        self.assertEqual(len(events),9,events)

if __name__=="__main__":unittest.main()
