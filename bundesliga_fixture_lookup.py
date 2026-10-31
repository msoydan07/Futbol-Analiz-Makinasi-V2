"""Official DFL fixtures: exact row matching, UTC kickoff, seven-day gate."""
import json,sys,urllib.request,unicodedata,re
from html.parser import HTMLParser
from datetime import datetime,timedelta,timezone
URL="https://products.bundesliga.com/fixtures"
class Tables(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None;self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.hidden+=1
  if tag=="tr":self.row=[]
  if tag in ("td","th") and self.row is not None:self.cell=[]
 def handle_data(self,data):
  if self.cell is not None and not self.hidden:self.cell.append(data)
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.hidden=max(0,self.hidden-1)
  if tag in ("td","th") and self.cell is not None:
   self.row.append(" ".join("".join(self.cell).split()));self.cell=None
  if tag=="tr" and self.row is not None:self.rows.append(self.row);self.row=None
def norm(x):
 x=unicodedata.normalize("NFKD",x.casefold())
 return "".join(c for c in x if c.isalnum() and not unicodedata.combining(c))
def lookup(home,away,now=None,html=None):
 now=now or datetime.now(timezone.utc)
 try:
  if html is None:
   req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en"})
   with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode("utf-8","replace")
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"official_source_unavailable","detail":str(e)[:140]}
 p=Tables();p.feed(html)
 hits=[]
 for row in p.rows:
  if len(row)<7:continue
  # DFL columns: Matchday, Day, Date, CET, UTC, Home, Away
  date,utc,team_h,team_a=row[1].split("|")[-1].strip(),row[3],row[4],row[5]
  if norm(team_h)!=norm(home) or norm(team_a)!=norm(away):continue
  try:kick=datetime.strptime(date+" "+utc,"%d-%b-%Y %H:%M").replace(tzinfo=timezone.utc)
  except ValueError:continue
  hits.append(kick)
 if len(hits)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"rows_seen":len(p.rows),"sample_rows":p.rows[:3]}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat(),"source_url":URL}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: bundesliga_fixture_lookup.py HOME AWAY")
 result=lookup(sys.argv[1],sys.argv[2]);print(json.dumps(result,ensure_ascii=False,indent=2))
 if result["status"]!="VERIFIED_OFFICIAL_FIXTURE":raise SystemExit(1)
