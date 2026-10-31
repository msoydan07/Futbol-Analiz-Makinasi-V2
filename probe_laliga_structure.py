"""Diagnose official LaLiga match page before writing an unsafe parser."""
import json,urllib.request,re
from html.parser import HTMLParser
from pathlib import Path
URL="https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-11"
class P(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None;self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag=="tr":self.row=[]
  if tag in ("td","th") and self.row is not None:self.cell=[]
  if tag in ("p","div","li","br","tr","td"):self.parts.append("\n")
 def handle_data(self,data):
  self.parts.append(data)
  if self.cell is not None:self.cell.append(data)
 def handle_endtag(self,tag):
  if tag in ("td","th") and self.cell is not None:
   self.row.append(" ".join("".join(self.cell).split()));self.cell=None
  if tag=="tr" and self.row is not None:self.rows.append(self.row);self.row=None
def main():
 result={"url":URL,"status":"NOT_VERIFIED"}
 try:
  req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"es-ES,es;q=0.9"})
  with urllib.request.urlopen(req,timeout=20) as r:html=r.read(2500000).decode("utf-8","replace");result["http"]=r.status
  p=P();p.feed(html)
  lines=[" ".join(s.split()) for s in "".join(p.parts).splitlines() if s.strip()]
  anchors=[i for i,x in enumerate(lines) if "Athletic Club" in x or "Real Sociedad" in x or "01.11.2026" in x]
  result.update({"html_chars":len(html),"rows":len(p.rows),"sample_rows":p.rows[:4],"anchor_context":[lines[max(0,i-3):i+4] for i in anchors[:8]],"anchors":len(anchors),"json_ld":"application/ld+json" in html,"next_data":"__NEXT_DATA__" in html,"status":"DIAGNOSTIC_ONLY"})
 except Exception as e:result.update({"status":"SOURCE_FETCH_FAILED","error":str(e)[:200]})
 Path("data").mkdir(exist_ok=True)
 Path("data/laliga_structure_probe.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
