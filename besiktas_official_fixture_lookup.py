"""Live Beşiktaş official match-centre lookup for one named fixture.

No hard-coded kickoff acceptance: names and date/time must appear on fetched page.
"""
import re
import urllib.request
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
from tff_fixture_lookup import normalize

URL="https://www.bjk.com.tr/tr/mac_merkezi/canli/25491"
class Text(HTMLParser):
 def __init__(self): super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("div","p","h1","h2","h3","span","br","td"):self.parts.append(" ")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def lookup(home,away,now=None):
 now=now or datetime.now(timezone.utc)
 if normalize(home)!=normalize("Kasımpaşa") or normalize(away)!=normalize("Beşiktaş"):
  return {"status":"NOT_VERIFIED","reason":"unsupported_named_fixture"}
 try:
  req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=25) as response:
   raw=response.read()
   charset=response.headers.get_content_charset() or "utf-8"
  parser=Text();parser.feed(raw.decode(charset,errors="replace"))
  visible=" ".join("".join(parser.parts).split())
 except Exception as exc:
  return {"status":"NOT_VERIFIED","reason":"official_club_page_unavailable","detail":str(exc)[:150]}
 # Official match title must be present, in home-away order.
 if not re.search(r"KASIMPAŞA\s*[-–]\s*BEŞİKTAŞ",visible,re.I):
  return {"status":"NOT_VERIFIED","reason":"official_club_pairing_missing"}
 match=re.search(r"\b(\d{1,2})\s+KASIM\s+(20\d{2})\s+(\d{1,2})[.:](\d{2})\b",visible,re.I)
 if not match:
  return {"status":"NOT_VERIFIED","reason":"official_club_kickoff_missing"}
 day,year,hour,minute=map(int,match.groups())
 try:local=datetime(year,11,day,hour,minute,tzinfo=ZoneInfo("Europe/Istanbul"))
 except ValueError:return {"status":"NOT_VERIFIED","reason":"official_club_kickoff_invalid"}
 kickoff=local.astimezone(timezone.utc)
 if not now<=kickoff<=now+timedelta(days=7):
  return {"status":"OUTSIDE_WINDOW","reason":"not_within_next_7_days"}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,
         "kickoff_utc":kickoff.isoformat(),"kickoff_turkey":local.isoformat(),
         "source_url":URL,"retrieved_at_utc":now.isoformat(),
         "verification_method":"live_official_club_page"}
