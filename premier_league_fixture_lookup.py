"""Premier League official revised schedule, strict per-line match verification."""
import json,re,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
URL="https://www.premierleague.com/en/news/4688862/fixture-amendments-for-premier-league-matches-in-october-and-november/"
class Lines(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.hidden+=1
  if tag in ("p","div","li","h1","h2","h3","br"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.hidden=max(0,self.hidden-1)
  if tag in ("p","div","li","h1","h2","h3"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en-GB,en;q=0.9"})
   with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"source_unavailable","detail":str(e)[:120]}
 p=Lines();p.feed(html)
 lines=[" ".join(x.split()) for x in "".join(p.parts).splitlines() if x.strip()]
 day_re=re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2}) (October|November)(?: 2026)?$",re.I)
 match_re=re.compile(r"^(?:(\d{1,2}:\d{2})(?: GMT)? )?(.+?) v (.+?)(?: \([^)]*\))?(?:\*)?$",re.I)
 aliases={"manutd":"manchesterunited","mancity":"manchestercity","spurs":"tottenhamhotspur","bournemouth":"afcbournemouth","nottmforest":"nottinghamforest","brighton":"brightonhovealbion","newcastle":"newcastleunited"}
 def canonical(x):return aliases.get(norm(x),norm(x))
 hits=[];date=None
 for line in lines:
  dm=day_re.match(line)
  if dm:date=datetime.strptime(dm.group(2)+" "+dm.group(3)+" 2026","%d %B %Y").date();continue
  if not date:continue
  mm=match_re.match(line)
  if not mm:continue
  time,h,a=mm.groups()
  if canonical(h)!=canonical(home) or canonical(a)!=canonical(away):continue
  if not time:return {"status":"NOT_VERIFIED","reason":"kickoff_not_confirmed","source_url":URL}
  local=datetime.strptime(str(date)+" "+time,"%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/London"))
  hits.append(local.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"sample":lines[:12]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: premier_league_fixture_lookup.py HOME AWAY")
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":raise SystemExit(1)
