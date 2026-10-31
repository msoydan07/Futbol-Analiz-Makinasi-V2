"""Single real-source smoke test: official TFF match detail, not a generic fixture scraper."""
import re,urllib.request,json
from html.parser import HTMLParser
from pathlib import Path
URL="https://www.tff.org/Default.aspx?macId=317866&pageId=29"
class Reader(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("td","tr","div","p","br"):self.parts.append(" ")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def main():
 req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
 try:
  with urllib.request.urlopen(req,timeout=25) as r:raw=r.read()
  p=Reader();p.feed(raw.decode("utf-8",errors="replace"))
  text=re.sub(r"\s+"," "," ".join(p.parts)).upper()
  home="KASIMPAŞA" in text or "KASIMPASA" in text
  away="BEŞİKTAŞ" in text or "BESIKTAS" in text
  date=bool(re.search(r"1\.11\.2026\s*[-–]\s*19:00",text))
  status="PASS" if home and away and date else "FAIL"
  result={"status":status,"source":URL,"home_found":home,"away_found":away,"kickoff_found":date,"method":"official_match_detail_html"}
 except Exception as e:
  result={"status":"SOURCE_UNAVAILABLE","source":URL,"error":str(e)[:160]}
 Path("data").mkdir(exist_ok=True)
 Path("data/tff_official_detail_smoke.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False))
 if result["status"]!="PASS":raise SystemExit("TFF official source smoke test failed")
if __name__=="__main__":main()
