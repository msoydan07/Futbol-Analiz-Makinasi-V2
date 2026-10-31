"""Official Lega Serie A match verification from dated referee announcements."""
import json,re,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
URL="https://en.legaseriea.it/serie-a/news/the-referees-for-the-10th-round-x4878"
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("p","div","li","br","h2","h3"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
  if tag in ("p","div","li"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en"})
   with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"official_source_unavailable","detail":str(e)[:120]}
 p=Text();p.feed(html);lines=[" ".join(x.split()) for x in "".join(p.parts).splitlines() if x.strip()]
 pattern=re.compile(r"^(.+?)\s+[–—-]\s+(.+?)\s+(?:(\d{2}/\d{2})\s+)?h\.\s*(\d{1,2})\.(\d{2})$",re.I)
 hits=[]
 for line in lines:
  m=pattern.match(line)
  if not m:continue
  h,a,day,hh,mm=m.groups()
  if norm(h)!=norm(home) or norm(a)!=norm(away):continue
  if not day:return {"status":"NOT_VERIFIED","reason":"date_missing_in_official_row","source_url":URL}
  try:local=datetime.strptime(day+"/2026 "+hh+":"+mm,"%d/%m/%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Rome"))
  except ValueError:continue
  hits.append(local.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"sample_matches":[x for x in lines if norm(home) in norm(x)][:3]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: serie_a_fixture_lookup.py HOME AWAY")
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":raise SystemExit(1)
