"""TFF weekly Super Lig fixture lookup: one requested match, official source only."""
import json,re,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

URL="https://www.tff.org/default.aspx?ftxtID=2966&pageID=600"
class Cells(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("tr","td","br","div","p","h2"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
  if tag in ("tr","td","div","p"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def normalize(value):
 value=value.upper().replace("İ","I").replace("ı","I")
 value="".join(x for x in unicodedata.normalize("NFKD",value) if not unicodedata.combining(x))
 value=re.sub(r"\b(?:A\.?Ş\.?|FK|SPOR KULÜBÜ)\b"," ",value)
 return re.sub(r"[^A-Z0-9]","",value)
def read_lines():
 request=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
 with urllib.request.urlopen(request,timeout=25) as response:raw=response.read()
 parser=Cells();parser.feed(raw.decode("windows-1254",errors="replace"))
 return [re.sub(r"\s+"," ",x).strip() for x in "".join(parser.parts).splitlines() if x.strip()]
def lookup(home,away,now=None,lines=None):
 now=now or datetime.now(timezone.utc)
 try:lines=lines if lines is not None else read_lines()
 except Exception as e:return {"status":"NOT_VERIFIED","reason":"official_source_unavailable","detail":str(e)[:120]}
 start=next((i for i,x in enumerate(lines) if "Trendyol Süper Lig" in x),-1)
 end=next((i for i,x in enumerate(lines) if i>start and "Trendyol 1. Lig" in x),len(lines))
 if start<0:return {"status":"NOT_VERIFIED","reason":"super_lig_section_missing"}
 lines=lines[start:end]
 dates=re.compile(r"\b(\d{1,2}\.\d{1,2}\.20\d\d)\b")
 times=re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
 records=[]
 # A fixture row is bounded by the next date; do not mix different fixtures.
 for i,line in enumerate(lines):
  dm=dates.search(line)
  if not dm:continue
  next_date=next((j for j in range(i+1,len(lines)) if dates.search(lines[j])),len(lines))
  chunk=lines[i:next_date]
  chunktext=" ".join(chunk)
  tm=times.search(chunktext)
  if not tm:continue
  # Ignore referee and venue: team names must be in the section around the match time.
  after=normalize(chunktext[tm.end():])
  nh,na=normalize(home),normalize(away)
  hpos=after.find(nh) if nh else -1
  apos=after.find(na) if na else -1
  if hpos<0 or apos<=hpos:continue
  # Do not match across another kickoff time in the same date block.
  if apos-hpos>180 or times.search(after[hpos:apos]):continue
  try:local=datetime.strptime(dm.group(1)+" "+tm.group(0),"%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Istanbul"))
  except ValueError:continue
  records.append(local)
 if len(records)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(records)}
 kickoff=records[0].astimezone(timezone.utc)
 if not now<=kickoff<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW"}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kickoff.isoformat(),"kickoff_turkey":records[0].isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: python tff_fixture_lookup.py HOME AWAY")
 print(json.dumps(lookup(sys.argv[1],sys.argv[2]),ensure_ascii=False,indent=2))
