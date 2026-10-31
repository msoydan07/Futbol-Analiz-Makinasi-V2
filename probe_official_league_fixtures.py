"""One-pass diagnostic for every non-TFF official fixture source. Not an acceptance test."""
import json,re,urllib.request,urllib.error
from datetime import datetime,timezone
from html.parser import HTMLParser
from official_fixture_source_policy import OFFICIAL
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.hidden+=1
  if tag in ("tr","td","li","br","p","div","time"):self.parts.append(" ")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
def main():
 out={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"status":"DIAGNOSTIC_ONLY_NOT_VERIFIED","leagues":{}}
 for code,src in OFFICIAL.items():
  if code=="TUR1":continue
  entry={"url":src["url"],"authority":src["authority"],"status":"UNTESTED"}
  try:
   req=urllib.request.Request(src["url"],headers={"User-Agent":"Mozilla/5.0 (compatible; FixtureVerifier/1.0)","Accept-Language":"en-US,en;q=0.8"})
   with urllib.request.urlopen(req,timeout=18) as response:
    raw=response.read(2000000);entry["http_status"]=response.status;entry["final_url"]=response.url;entry["content_type"]=response.headers.get("Content-Type","")
   html=raw.decode("utf-8",errors="replace")
   p=Visible();p.feed(html);visible=re.sub(r"\s+"," "," ".join(p.parts))
   entry["html_bytes"]=len(raw);entry["visible_chars"]=len(visible)
   entry["date_pattern_hits"]=len(re.findall(r"\b(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})\b",visible))
   entry["time_pattern_hits"]=len(re.findall(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",visible))
   entry["has_structured_data"]="application/ld+json" in html
   entry["has_next_data"]="__NEXT_DATA__" in html
   entry["status"]="FETCHED_NEEDS_MATCH_PARSER" if entry["visible_chars"]>500 else "FETCHED_LOW_CONTENT"
   entry["sample"]=visible[:350]
  except Exception as e:entry["status"]="SOURCE_FETCH_FAILED";entry["error"]=str(e)[:180]
  out["leagues"][code]=entry
  print(code,entry["status"],entry.get("date_pattern_hits"),entry.get("time_pattern_hits"),flush=True)
 from pathlib import Path
 Path("data").mkdir(exist_ok=True)
 Path("data/official_league_probe.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
