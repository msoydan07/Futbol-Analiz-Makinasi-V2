"""KNVB Eredivisie official fixture rows, exact sequence and seven-day gate."""
import json,re,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
URL="https://www.knvb.nl/competities/eredivisie/programma"
MONTHS={"januari":1,"februari":2,"maart":3,"april":4,"mei":5,"juni":6,"juli":7,"augustus":8,"september":9,"oktober":10,"november":11,"december":12}
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("p","li","br","div","h2","h3","span"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
  if tag in ("p","li","div"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"nl-NL,nl;q=0.9"})
   with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"official_source_unavailable","detail":str(e)[:120]}
 p=Visible();p.feed(html);lines=[" ".join(s.split()) for s in "".join(p.parts).splitlines() if s.strip()]
 day_re=re.compile(r"^(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag) (\d{1,2}) (\w+) (20\d{2})$",re.I)
 time_re=re.compile(r"^\d{1,2}:\d{2}$")
 date=None;hits=[]
 for i,line in enumerate(lines):
  m=day_re.match(line)
  if m:
   try:date=datetime(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1))).date()
   except (KeyError,ValueError):date=None
   continue
  if date and norm(line)==norm(home) and i+2<len(lines) and time_re.match(lines[i+1]) and norm(lines[i+2])==norm(away):
   local=datetime.strptime(str(date)+" "+lines[i+1],"%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Amsterdam"))
   hits.append(local.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines)}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: eredivisie_fixture_lookup.py HOME AWAY")
 result=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(result,ensure_ascii=False,indent=2))
 if result["status"]!="VERIFIED_OFFICIAL_FIXTURE":raise SystemExit(1)
