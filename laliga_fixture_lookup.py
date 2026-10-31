"""LaLiga official JSON-LD SportsEvent: strict teams, kickoff and seven-day window."""
import json,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
URL="https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-11"
class Scripts(HTMLParser):
 def __init__(self):super().__init__();self.collect=False;self.parts=[];self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=="script" and dict(attrs).get("type","").lower()=="application/ld+json":self.collect=True;self.parts=[]
 def handle_data(self,data):
  if self.collect:self.parts.append(data)
 def handle_endtag(self,tag):
  if tag=="script" and self.collect:self.scripts.append("".join(self.parts));self.collect=False
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def events(obj):
 if isinstance(obj,list):
  for item in obj:yield from events(item)
 elif isinstance(obj,dict):
  if obj.get("@type")=="SportsEvent":yield obj
  for k in ("@graph","itemListElement"):
   if k in obj:yield from events(obj[k])
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"es-ES,es;q=0.9"})
   with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"official_source_unavailable","detail":str(e)[:120]}
 p=Scripts();p.feed(html);matches=[];total=0
 for script in p.scripts:
  try:data=json.loads(script)
  except ValueError:continue
  for event in events(data):
   total+=1
   h=event.get("homeTeam") or {};a=event.get("awayTeam") or {}
   if not isinstance(h,dict) or not isinstance(a,dict):continue
   if norm(h.get("name",""))!=norm(home) or norm(a.get("name",""))!=norm(away):continue
   try:kick=datetime.fromisoformat(event["startDate"].replace("Z","+00:00"))
   except (ValueError,KeyError,TypeError):continue
   if kick.tzinfo is None:continue
   matches.append(kick.astimezone(timezone.utc))
 if len(matches)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(matches),"events_seen":total,"scripts_seen":len(p.scripts)}
 kick=matches[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: laliga_fixture_lookup.py HOME AWAY")
 result=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(result,ensure_ascii=False,indent=2))
 if result["status"]!="VERIFIED_OFFICIAL_FIXTURE":raise SystemExit(1)
