"""Batch source audit: official fixture page structure for remaining leagues."""
import json,re,urllib.request
from html.parser import HTMLParser
from pathlib import Path
SOURCES={
"FRA1":"https://ligue1.com/fr/articles/l1_article_5805-",
"NED1":"https://www.knvb.nl/competities/eredivisie/programma",
"POR1":"https://www.ligaportugal.pt/",
"BEL1":"https://www.proleague.be/",
"ENG2":"https://www.efl.com/matches/",
}
NEEDLES={"FRA1":["OGC Nice","Stade Rennais","Samedi 31","31 octobre"],"NED1":["Feyenoord","Fortuna Sittard","31 oktober"],"POR1":["2026","Novembro","Liga Portugal"],"BEL1":["2026","Jupiler","kalender"],"ENG2":["Championship","October","2026"]}
class Extract(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.scripts=0;self.skip=0;self.rows=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag=="tr":self.rows+=1
  if tag in ("p","li","br","tr","td","h1","h2","h3","div"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
  if tag in ("p","li","tr","div"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def main():
 result={}
 for league,url in SOURCES.items():
  d={"url":url,"status":"NOT_VERIFIED"}
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en,fr,nl,pt;q=0.8"})
   with urllib.request.urlopen(req,timeout=15) as r:html=r.read(2000000).decode("utf-8","replace");d["http"]=r.status
   p=Extract();p.feed(html)
   lines=[" ".join(s.split()) for s in "".join(p.parts).splitlines() if s.strip()]
   indices=[i for i,s in enumerate(lines) if any(n.casefold() in s.casefold() for n in NEEDLES[league])]
   d.update({"status":"FETCHED_DIAGNOSTIC_ONLY","html_chars":len(html),"rows":p.rows,"visible_lines":len(lines),"json_ld":"application/ld+json" in html,"next_data":"__NEXT_DATA__" in html,"contexts":[lines[max(0,i-2):i+5] for i in indices[:6]],"initial_lines":lines[:8]})
  except Exception as e:d.update({"status":"SOURCE_FETCH_FAILED","error":str(e)[:200]})
  result[league]=d
 Path("data").mkdir(exist_ok=True)
 Path("data/remaining_leagues_batch_probe.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
