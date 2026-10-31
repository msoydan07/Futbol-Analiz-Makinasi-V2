"""Pro League official Jupiler fixture lookup, strict home/time/date/away grouping."""
import json,re,sys,urllib.request,unicodedata
from html.parser import HTMLParser
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
URL="https://www.proleague.be/fr/jpl-calendar"
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,attrs):
  if t in ("script","style"):self.skip+=1
  if t in ("p","div","li","h2","h3","span","br"):self.a.append("\n")
 def handle_endtag(self,t):
  if t in ("script","style"):self.skip=max(0,self.skip-1)
  if t in ("p","div","li"):self.a.append("\n")
 def handle_data(self,x):
  if not self.skip:self.a.append(x)
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"fr"})
   with urllib.request.urlopen(req,timeout=20) as f:html=f.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"source_unavailable","detail":str(e)[:120]}
 p=Visible();p.feed(html);lines=[" ".join(x.split()) for x in "".join(p.a).splitlines() if x.strip()]
 date_re=re.compile(r"^(?:lun|mar|mer|jeu|ven|sam|dim)\.\s*(\d{1,2})\s*(oct|nov)\.$",re.I)
 time_re=re.compile(r"^\d{1,2}:\d{2}$")
 hits=[]
 for i,line in enumerate(lines):
  if norm(line)!=norm(home):continue
  # The official card order is home, kickoff time, abbreviated date, away.
  if i+3>=len(lines) or not time_re.fullmatch(lines[i+1]):continue
  dm=date_re.fullmatch(lines[i+2])
  if not dm or norm(lines[i+3])!=norm(away):continue
  month=10 if dm.group(2).lower()=="oct" else 11
  day=int(dm.group(1))
  try:local=datetime.strptime(f"2026-{month:02d}-{day:02d} {lines[i+1]}","%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Brussels"))
  except ValueError:continue
  hits.append(local.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"context":[lines[max(0,i-2):i+7] for i,x in enumerate(lines) if norm(x)==norm(home)][:2]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":sys.exit(1)
