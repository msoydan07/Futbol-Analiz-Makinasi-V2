"""Official Belgian Jupiler Pro League timed fixtures from SSR Next.js JSON.

The rendered football cards omit text timestamps, but the official website's
#__NEXT_DATA__ pageProps.data.page.grids[].areas[].modules[].data.matches
contains explicit ISO UTC kickoffs and exact home/away names. No guesses.
"""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

PARSER="belgium_proleague_nextjs_jpl"
OFFICIAL_URL="https://www.proleague.be/jpl-kalender!"
BRUSSELS=ZoneInfo("Europe/Brussels")
SEASON=re.compile(r'^Seizoen (20\d\d)/(20\d\d)$')
DATE=re.compile(r'^20\d\d-\d\d-\d\d$')
STOP=("cancel","postpon","reschedul","abandon","verschoven","afgelast")
class _Next(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active=False;self.blocks=[];self.current=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script" and dict(attrs).get("id")=="__NEXT_DATA__":
            self.active=True;self.current=[]
    def handle_data(self,data):
        if self.active:self.current.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self.active:
            self.blocks.append("".join(self.current))
            self.active=False

def parse_proleague(html):
    if not isinstance(html,str) or len(html)>2_000_000:return []
    parser=_Next();parser.feed(html)
    if len(parser.blocks)!=1:return []
    try:
        data=json.loads(parser.blocks[0])
        page=data["props"]["pageProps"]["data"]["page"]
        modules=[m for grid in page["grids"] for area in grid["areas"]
                 for m in area["modules"] if isinstance(m,dict)]
    except (ValueError,KeyError,TypeError):return []
    matches=[]
    for module in modules:
        block=module.get("data")
        if not isinstance(block,dict):continue
        rows=block.get("matches")
        if not isinstance(rows,list):continue
        for m in rows:
            if isinstance(m,dict):matches.append(m)
    if not 1<=len(matches)<=50:return []
    out=[];by_id={}
    for m in matches:
        try:
            if m["competition"]["name"]!="Jupiler Pro League":continue
            season=SEASON.fullmatch(m["season"]["name"])
            if not season or int(season.group(2))!=int(season.group(1))+1:continue
            period=str(m.get("period",{}).get("type","")).lower()
            if any(x in period for x in STOP):continue
            if not DATE.fullmatch(m["date"]):continue
            iso=m["time"]
            instant=datetime.fromisoformat(iso.replace("Z","+00:00"))
            if instant.tzinfo is None:continue
            utc=instant.astimezone(timezone.utc)
            if not int(season.group(1))<=utc.year<=int(season.group(2)):continue
            if utc.astimezone(BRUSSELS).date().isoformat()!=m["date"]:continue
            home=m["homeTeam"]["name"].strip()
            away=m["awayTeam"]["name"].strip()
            identifier=m["id"]
            if not isinstance(identifier,str) or not identifier or not home or not away or home.casefold()==away.casefold():continue
        except (ValueError,TypeError,KeyError,AttributeError):continue
        key=(home,away,utc.isoformat())
        if identifier in by_id and by_id[identifier]!=key:return []
        by_id[identifier]=key
        out.append({"home":home,"away":away,"match_date":m["date"],
                    "kickoff_utc":utc.isoformat(),"format":PARSER})
    return out
