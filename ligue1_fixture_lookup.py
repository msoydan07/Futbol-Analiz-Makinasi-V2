"""Official Ligue 1 fixture lookup from updated PSG matchweek schedule."""
import json,re,sys,urllib.request,unicodedata
from html.parser import HTMLParser
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
URL="https://www.psg.fr/en/content/ligue-1-matchday-9-fixtures-2026-2027-havre-ac-paris-saint-germain"
class Text(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,attrs):
  if t in ("script","style"):self.skip+=1
  if t in ("p","div","li","h2","h3","br"):self.a.append("\n")
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
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
   with urllib.request.urlopen(req,timeout=20) as f:html=f.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"source_unavailable","detail":str(e)[:120]}
 p=Text();p.feed(html);lines=[" ".join(x.split()) for x in "".join(p.a).splitlines() if x.strip()]
 date_re=re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2})(?:st|nd|rd|th)? (October|November) 2026 (\d{1,2})(?:\.(\d{2}))?\s*(am|pm)",re.I)
 date=None;hits=[]
 for line in lines:
  m=date_re.match(line)
  if m:
   hour=int(m.group(4))%12+(12 if m.group(6).lower()=="pm" else 0)
   minute=int(m.group(5) or 0)
   date=datetime.strptime(f"{m.group(2)} {m.group(3)} 2026","%d %B %Y").replace(hour=hour,minute=minute,tzinfo=ZoneInfo("Europe/Paris"))
   continue
  if date and (" - " in line or " – " in line):
   bits=re.split(r"\s+[-–]\s+",line,maxsplit=1)
   if len(bits)==2 and norm(bits[0])==norm(home) and norm(bits[1])==norm(away):hits.append(date.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"samples":[x for x in lines if norm(home) in norm(x)][:3]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"source_authority":"Paris Saint-Germain official club schedule","retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":sys.exit(1)
