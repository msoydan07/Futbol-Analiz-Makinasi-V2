"""One strictly scoped official Liga Portugal Betclic November 2026 news parser.

The public Nuxt HTML embeds the exact nine televised Jornada 11 match lines
inside escaped article markup. This parser does NOT infer fixtures from general
news prose or treat lower-division / calendar abbreviations as top-flight data.
"""
from __future__ import annotations
import html as html_lib,re
from datetime import datetime,timezone
from zoneinfo import ZoneInfo

SOURCE_URL="https://www.ligaportugal.pt/news/29039/media-kits-jornada-11-da-liga-portugal-betclic"
PARSER="liga_portugal_betclic_news_j11_2026"
COUNTS={6:1,7:3,8:5}
DAYS={"Sexta-feira":6,"Sábado":7,"Domingo":8}
ROW=re.compile(r'^(.{2,90}?)\s+[-–]\s+(.{2,90}?),\s*(\d{1,2})h([0-5]\d)\s*[-–]\s*(?:SportTV|TVI|BTV|Sport TV)',re.I)
DAY=re.compile(r'^(Sexta-feira|Sábado|Domingo),\s*(\d{1,2})\s+de\s+novembro$',re.I)
START="Fique a par da jornada completa e de todas as curiosidades dos nove jogos da ronda."

def parse_news(html):
    if not isinstance(html,str) or not 100<=len(html)<=2_000_000:
        return []
    if ("Media Kits - Jornada 11 da Liga Portugal Betclic" not in html
        or START not in html):
        return []
    # Only the literal escaped <p> section in the first occurrence of the
    # official current round article. Refuse to parse generic duplicated prose.
    start=html.find(START)
    snippet=html[start:start+6500]
    if r"\u003C" not in snippet:return []
    decoded=(snippet.replace(r"\u003C","<").replace(r"\u003E",">")
             .replace(r"\u0026","&").replace(r'\"','"'))
    lines=[html_lib.unescape(t).strip() for t in re.sub(r"<[^>]*>","\n",decoded).splitlines()]
    matches=[];day=None;count={}
    for line in lines:
        if not line:continue
        m=DAY.fullmatch(line)
        if m:
            expected=DAYS.get(m.group(1))
            if expected!=int(m.group(2)):return []
            day=expected;count.setdefault(day,0);continue
        m=ROW.fullmatch(line)
        if not m:continue
        if day is None:return []
        home,away,h,mn=m.groups()
        home,away=home.strip(),away.strip()
        hh=int(h)
        if hh>23 or not home or not away or home.casefold()==away.casefold():return []
        dt=datetime(2026,11,day,hh,int(mn),tzinfo=ZoneInfo("Europe/Lisbon"))
        if (dt.astimezone(timezone.utc).date().isoformat()!="2026-11-%02d"%day):
            return []
        matches.append({"home":home,"away":away,
                        "match_date":dt.date().isoformat(),
                        "kickoff_utc":dt.astimezone(timezone.utc).isoformat(),
                        "format":PARSER})
        count[day]+=1
    if (count!=COUNTS or len(matches)!=9 or
        len({(m["home"],m["away"],m["kickoff_utc"]) for m in matches})!=9):
        return []
    return matches
