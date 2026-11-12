"""Fallback-only official EFL Sky Sports *selected* Championship fixtures.

Source is an EFL 2026/27 TV selection table. It is NOT the full Championship
fixture list, never an independent proof that no other matches are scheduled.
"""
from __future__ import annotations
import re
from datetime import datetime,timezone,date
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

PARSER="efl_2026_27_official_tv_selection"
SOURCE_URL="https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/"
LONDON=ZoneInfo("Europe/London")
DATE_RE=re.compile(r"\d{2}-[A-Za-z]{3}-\d{2}")
TIME_RE=re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")

class _Table(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.row=[]
        if tag in ("td","th") and self.row is not None:self.cell=[]
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()));self.cell=None
        if tag=="tr" and self.row is not None:
            self.rows.append(self.row);self.row=None
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)

def parse_efl_tv(html):
    if not isinstance(html,str) or not 50<=len(html)<=2_000_000:return []
    if "Sky Sports" not in html or "Championship" not in html:return []
    p=_Table();p.feed(html)
    if not p.rows:
        # The live official news page contains its TV table as serialized
        # article HTML inside a script. The normal HTML parser correctly
        # doesn't treat those tags as DOM rows; isolate only the explicitly
        # dated official table and parse it as a separate fragment.
        probe=html.find("21-Nov-26")
        start=html.rfind("<table",0,probe) if probe>=0 else -1
        finish=html.find("</table>",probe) if probe>=0 else -1
        if 0<=start<probe<finish and finish-start<=500_000:
            fragment=html[start:finish+8].replace(r"\n","\n")
            p=_Table();p.feed(fragment)
    rows=[];pairs=set()
    for line in p.rows:
        if len(line)<7 or line[0].casefold() not in ("championship","sky bet championship"):
            continue
        if not DATE_RE.fullmatch(line[1]) or not TIME_RE.fullmatch(line[3]):
            continue
        if line[5].casefold() not in ("v","vs"):continue
        try:local=datetime.strptime(line[1]+" "+line[3],"%d-%b-%y %H:%M").replace(tzinfo=LONDON)
        except ValueError:continue
        if not date(2026,8,1)<=local.date()<=date(2027,5,31):continue
        home=line[4].strip();away=line[6].strip()
        if not home or not away or home.casefold()==away.casefold():continue
        utc=local.astimezone(timezone.utc)
        key=(home,away,local.date().isoformat())
        if key in pairs:
            return [] # ambiguous official duplicate, never select one timestamp
        pairs.add(key)
        rows.append({"home":home,"away":away,
                     "match_date":local.date().isoformat(),
                     "kickoff_utc":utc.isoformat(),
                     "format":PARSER})
    return rows
