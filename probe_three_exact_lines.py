"""Inspect exact official match source line sequences for three unresolved leagues."""
import json,urllib.request
from html.parser import HTMLParser
from pathlib import Path
SOURCES={"BEL1":"https://kvmechelen.be/kalender/","POR1":"https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada","ENG2":"https://www.efl.com/news/2026/october/29/referee-appointments--30-october-4-november/"}
TERMS={"BEL1":["Genk","Mechelen","oktober","16:00"],"POR1":["Estoril","Porto","31 de outubro","20h30"],"ENG2":["Blackburn","Stoke","Tuesday 3","Championship"]}
class P(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,attrs):
  if t in ("script","style"):self.skip+=1
  if t in ("p","div","li","h1","h2","h3","h4","br"):self.a.append("\n")
 def handle_endtag(self,t):
  if t in ("script","style"):self.skip=max(0,self.skip-1)
  if t in ("p","div","li"):self.a.append("\n")
 def handle_data(self,x):
  if not self.skip:self.a.append(x)
out={}
for key,url in SOURCES.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en,pt,nl"})
  with urllib.request.urlopen(req,timeout=20) as f:h=f.read(2500000).decode("utf-8","replace")
  p=P();p.feed(h);lines=[" ".join(x.split()) for x in "".join(p.a).splitlines() if x.strip()]
  indices=[i for i,x in enumerate(lines) if any(t.lower() in x.lower() for t in TERMS[key])]
  out[key]={"status":"FETCHED","total_lines":len(lines),"contexts":[{"line":i,"text":lines[max(0,i-4):i+7]} for i in indices[:12]]}
 except Exception as e:out[key]={"status":"ERROR","error":str(e)[:150]}
Path("data").mkdir(exist_ok=True)
Path("data/three_exact_line_diagnostics.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
