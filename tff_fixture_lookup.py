"""TFF weekly Super Lig fixture lookup: one requested match, official source only."""
import json,re,sys,urllib.request,unicodedata
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

URL="https://www.tff.org/Default.aspx?hafta=10&pageId=198"
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
 # Only the official Super Lig section, not any other league or archived season.
 start=next((i for i,x in enumerate(lines) if "TRENDYOLSUPERLIG" in normalize(x) and "HAFTA" in normalize(x)),-1)
 if start<0:return {"status":"NOT_VERIFIED","reason":"super_lig_section_missing","sample":lines[:8]}
 end=next((i for i in range(start+1,len(lines)) if "TRENDYOL1LIG" in normalize(lines[i]) and "HAFTA" in normalize(lines[i])),len(lines))
 lines=lines[start:end]
 date_re=re.compile(r"\b(\d{1,2}\.\d{1,2}\.20\d\d)\b")
 time_re=re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
 dates=[(i,date_re.search(line)) for i,line in enumerate(lines) if date_re.search(line)]
 records=[]
 nh,na=normalize(home),normalize(away)
 for index,(i,dm) in enumerate(dates):
  stop=dates[index+1][0] if index+1<len(dates) else len(lines)
  block=lines[i:stop]
  # Split multiple matches on the same date by kickoff time.
  time_positions=[(j,time_re.search(line)) for j,line in enumerate(block) if time_re.search(line)]
  for k,(j,tm) in enumerate(time_positions):
   finish=time_positions[k+1][0] if k+1<len(time_positions) else len(block)
   segment=normalize(" ".join(block[j+1:finish]))
   hpos=segment.find(nh) if nh else -1
   apos=segment.find(na) if na else -1
   if hpos<0 or apos<=hpos or apos-hpos>180:continue
   try:local=datetime.strptime(dm.group(1)+" "+tm.group(0),"%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Istanbul"))
   except ValueError:continue
   records.append(local)
 if len(records)!=1:return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(records),"diagnostics":{"lines":len(lines),"date_count":len(dates),"sample":lines[:12]}}
 kickoff=records[0].astimezone(timezone.utc)
 if not now<=kickoff<=now+timedelta(days=7):return {"status":"OUTSIDE_WINDOW"}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kickoff.isoformat(),"kickoff_turkey":records[0].isoformat(),"source_url":URL,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("Usage: python tff_fixture_lookup.py HOME AWAY")
 print(json.dumps(lookup(sys.argv[1],sys.argv[2]),ensure_ascii=False,indent=2))
