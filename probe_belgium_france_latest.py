"""Belgian Pro League official calendar structural probe, plus updated French schedule notice."""
import json,urllib.request
from html.parser import HTMLParser
from pathlib import Path
URLS={"BEL1":"https://www.proleague.be/fr/jpl-calendar","FRA1_LATEST":"https://ligue1.com/fr/articles/l1_article_6009-"}
class P(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
  if tag in ("p","li","div","h1","h2","h3","span","br"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.skip=max(0,self.skip-1)
  if tag in ("p","li","div"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
result={}
for key,url in URLS.items():
 r={"url":url,"status":"NOT_VERIFIED"}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"fr-FR,fr;q=0.9"})
  with urllib.request.urlopen(req,timeout=20) as f:html=f.read(1500000).decode("utf-8","replace");r["http"]=f.status
  p=P();p.feed(html);lines=[" ".join(x.split()) for x in "".join(p.parts).splitlines() if x.strip()]
  anchors=[i for i,x in enumerate(lines) if any(n in x.lower() for n in (("mechelen","genk","31 oct","anderlecht") if key=="BEL1" else ("nice","rennes","30 octobre","31 octobre")))]
  r.update({"status":"STRUCTURE_ONLY","lines":len(lines),"contexts":[lines[max(0,i-3):i+5] for i in anchors[:12]],"first_lines":lines[:8],"json_ld":"application/ld+json" in html})
 except Exception as e:r.update({"status":"SOURCE_FETCH_FAILED","error":str(e)[:180]})
 result[key]=r
Path("data").mkdir(exist_ok=True)
Path("data/belgium_france_latest_probe.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False,indent=2))
