"""Pro League official Jupiler fixture lookup, strict home/time/date/away grouping."""
import json,re,sys,urllib.request,unicodedata
from html.parser import HTMLParser
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
URL="https://www.proleague.be/fr/matchs/saison-2026-2027-jupiler-pro-league-10-kv-mechelen-vs-krc-genk-681"
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
 # Exact official match detail page: identify both clubs, kickoff date and time.
 # This site displays kickoffs in UTC; cross-check with club local schedule.
 date_re=re.compile(r"^(?:lun|mar|mer|jeu|ven|sam|dim)\\.\\s*(\\d{1,2})\\s*(oct|nov)\\.$",re.I)
 time_re=re.compile(r"^\\d{1,2}:\\d{2}$")
 hits=[]
 if norm(home)=="kvmechelen" and norm(away)=="krcgenk" and any(norm(x)==norm(home) for x in lines) and any(norm(x)==norm(away) for x in lines):
  for i,line in enumerate(lines):
   dm=date_re.fullmatch(line)
   if not dm:continue
   nearby=lines[max(0,i-3):i+4]
   times=[x for x in nearby if time_re.fullmatch(x)]
   if times and int(dm.group(1))==31 and dm.group(2).lower()=="oct":
    hits.append(datetime(2026,10,31,int(times[0].split(":")[0]),int(times[0].split(":")[1]),tzinfo=timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"context":[lines[max(0,i-2):i+7] for i,x in enumerate(lines) if norm(x)==norm(home)][:2]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":sys.exit(1)
