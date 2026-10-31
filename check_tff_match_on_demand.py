"""Fetch TFF's official weekly program and verify a requested Süper Lig match.
Only on-demand, within 7 days; no full-season archive or secondary provider.
"""
import re,urllib.request
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
from verify_match_on_demand import verify_requested_fixture

TFF_URL="https://www.tff.org/default.aspx?ftxtID=2966&pageID=600"
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.words=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.hidden+=1
  if tag in ("tr","td","p","div","br","h1","h2","h3"):self.words.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.hidden=max(0,self.hidden-1)
  if tag in ("tr","td","p","div"):self.words.append("\n")
 def handle_data(self,data):
  if not self.hidden:self.words.append(data)
def text_from_html(payload):
 p=Visible();p.feed(payload);return re.sub(r"\s+"," "," ".join(p.words)).strip()
def check_tff_match(home,away,now=None,registry_path="data/match_registry.json"):
 now=now or datetime.now(timezone.utc)
 req=urllib.request.Request(TFF_URL,headers={"User-Agent":"Mozilla/5.0 (compatible; FutbolAnalizV2/1.0)"})
 try:
  with urllib.request.urlopen(req,timeout=25) as response:
   html=response.read().decode("utf-8-sig",errors="replace")
 except Exception as exc:
  return {"status":"NOT_VERIFIED","reason":"official_page_unavailable","detail":str(exc)[:140]}
 content=text_from_html(html)
 # Source contains official local Turkish times; reject if requested pairing is not uniquely found.
 h=re.escape(home);a=re.escape(away)
 # Teams are supplied in the source's official display form, not guessed aliases.
 pattern=re.compile(r"(\d{2}\.\d{2}\.\d{4}).{0,130}?(\d{1,2}:\d{2}).{0,280}?"+h+r".{0,280}?"+a,re.I)
 matches=list(pattern.finditer(content))
 if len(matches)!=1:
  return {"status":"NOT_VERIFIED","reason":"official_fixture_not_uniquely_extracted","matches":len(matches)}
 match=matches[0]
 try:
  local=datetime.strptime(match.group(1)+" "+match.group(2),"%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Istanbul"))
 except ValueError:
  return {"status":"NOT_VERIFIED","reason":"official_kickoff_parse_failed"}
 if not now<=local.astimezone(timezone.utc)<=now+timedelta(days=7):
  return {"status":"OUTSIDE_WINDOW","reason":"not_within_next_7_days"}
 return verify_requested_fixture("TUR1",home,away,local.isoformat(),TFF_URL,now.isoformat(),now=now,source_checked=True,registry_path=registry_path)
