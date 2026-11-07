"""One-batch official HTML parser diagnostic, no model, no forecast, no bookmaker."""
from __future__ import annotations
import json,hashlib
from official_page_lookup_263 import _default_fetch,_Markup,parse_official_events
from pathlib import Path
CASES={
 'ENG2':['https://www.efl.com/','https://www.efl.com/news/2026/november/05/referee-appointments--6---8-november/'],
 'GER1':['https://products.bundesliga.com/fixtures'],
 'POR1':['https://www.ligaportugal.pt/calendar','https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada',
         'https://www.ligaportugal.pt/news/29039/media-kits-jornada-11-da-liga-portugal-betclic'],
 'BEL1':['https://www.proleague.be/jpl-kalender!'],
 'ESP1':['https://www.laliga.com/iframes/external-consumer-broadcast'],
 'TUR1':['https://www.tff.org/Default.aspx?macId=317878&pageId=29']}
TOKENS={
 'ENG2':['Wrexham','Wolverhampton','Blackburn','Watford'],
 'GER1':['Dortmund','Elversberg','Paderborn','Stuttgart'],
 'POR1':['Nacional','Académico','Alverca','Sporting','Moreirense'],
 'BEL1':['Westerlo','Charleroi','OH Leuven','Lommel'],
 'ESP1':['Málaga','Racing Club','Espanyol','Deportivo','Osasuna'],
 'TUR1':['GÖZTEPE','BAŞAKŞEHİR','7.11.2026']}
def probe():
    reports=[]
    for league,urls in CASES.items():
        for url in urls:
            row={'league':league,'url':url}
            try:
                effective,html=_default_fetch(url,league)
                m=_Markup();m.feed(html)
                lines=[' '.join(x.split()) for x in ''.join(m.visible).splitlines() if x.strip()]
                text=' '.join(lines)
                row.update(effective=effective,html_length=len(html),html_sha256=hashlib.sha256(html.encode()).hexdigest(),
                           rows_count=len(m.rows),row_examples=m.rows[:3],visible_count=len(lines),
                           visible_examples=lines[:32],token_snippets={
                               name:text[max(0,text.casefold().find(name.casefold())-70):text.casefold().find(name.casefold())+170]
                               for name in TOKENS[league] if name.casefold() in text.casefold()},
                           parsed_count_default=len(parse_official_events(league,html)),
                           html_token_counts={name:html.casefold().count(name.casefold()) for name in TOKENS[league]})
            except Exception as e:row['error']=type(e).__name__+':'+str(e)[:180]
            reports.append(row)
            print(json.dumps({'league':league,'url':url,'error':row.get('error'),
                              'lines':row.get('visible_count'),'parsed':row.get('parsed_count_default'),
                              'tokens':row.get('html_token_counts')},ensure_ascii=False))
    Path('/tmp/263_official_26_html_diag.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':probe()
