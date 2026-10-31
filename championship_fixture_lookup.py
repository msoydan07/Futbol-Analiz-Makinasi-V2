"""Official EFL Championship match appointment lookup, fail closed."""
import json,re,sys,urllib.request,unicodedata
from html.parser import HTMLParser
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
URL="https://www.efl.com/news/2026/october/29/referee-appointments--30-october-4-november/"
class Text(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,attrs):
  if t in ("script","style"):self.skip+=1
  if t in ("p","div","li","h2","h3","h4","br"):self.a.append("\n")
 def handle_endtag(self,t):
  if t in ("script","style"):self.skip=max(0,self.skip-1)
  if t in ("p","div","li"):self.a.append("\n")
 def handle_data(self,x):
  if not self.skip:self.a.append(x)
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold());return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
   with urllib.request.urlopen(req,timeout=20) as f:html=f.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"source_unavailable","detail":str(e)[:120]}
 p=Text();p.feed(html);lines=[" ".join(x.split()) for x in "".join(p.a).splitlines() if x.strip()]
 day_re=re.compile(r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2}) (October|November)$",re.I)
 match_re=re.compile(r"^(.+?)\s+v\s+(.+?)\s+\((\d{1,2}:\d{2})\)$",re.I)
 date=None;in_champ=False;hits=[]
 for line in lines:
  dm=day_re.fullmatch(line)
  if dm:
   date=datetime.strptime(f"{dm.group(1)} {dm.group(2)} 2026","%d %B %Y").date();in_champ=False;continue
  if "championship" in line.casefold() and len(line)<60:in_champ=True;continue
  if line.startswith("Sky Bet League") or line.startswith("EFL League") or line.startswith("Jersey Mike"):in_champ=False
  mm=match_re.fullmatch(line)
  if in_champ and date and mm and norm(mm.group(1))==norm(home) and norm(mm.group(2))==norm(away):
   local=datetime.strptime(str(date)+" "+mm.group(3),"%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/London"))
   hits.append(local.astimezone(timezone.utc))
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"samples":[x for x in lines if norm(home) in norm(x)][:4]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat()}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(r,ensure_ascii=False,indent=2))
 if r["status"]!="VERIFIED_OFFICIAL_FIXTURE":sys.exit(1)
