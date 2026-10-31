"""Fetch an actual official Premier League fixture article, extract candidate pairs.
No guessing of match kickoff or automatic acceptance of fixture completeness.
"""
import json,re,urllib.request
from datetime import date,datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
URL="https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-season-202627-premier-league-season"
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.hidden+=1
  if tag in ("p","h1","h2","h3","h4","li","br"):self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style"):self.hidden=max(0,self.hidden-1)
  if tag in ("p","h1","h2","h3","h4","li"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
def main():
 req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; FutbolAnalizV2/1.0)"})
 with urllib.request.urlopen(req,timeout=30) as response:
  payload=response.read().decode("utf-8",errors="replace")
 parser=Text();parser.feed(payload)
 lines=[re.sub(r"\\s+"," ",s).strip() for s in "".join(parser.parts).splitlines()]
 lines=[s for s in lines if s]
 months="January February March April May June July August September October November December".split()
 month_re="|".join(months)
 day_re=re.compile(r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\\s+(\\d{1,2})\\s+("+month_re+r")(?:\\s+(2026|2027))?",re.I)
 fixture_re=re.compile(r"^(?:(\\d{1,2}:\\d{2})\\s+)?(.+?)\\s+v\\s+(.+?)(?:\\s+\\([^)]*\\))?$",re.I)
 active=None;matches=[];year=2026
 for line in lines:
  m=day_re.match(line)
  if m:
   month=months.index(m.group(2).capitalize())+1
   year=int(m.group(3)) if m.group(3) else (2027 if month<=5 else 2026)
   try:active=date(year,month,int(m.group(1)))
   except ValueError:active=None
   continue
  if not active:continue
  m=fixture_re.match(line)
  if not m:continue
  home=m.group(2).strip();away=m.group(3).strip()
  if len(home)>60 or len(away)>60:continue
  matches.append({"league":"ENG1","season":"2026-2027","match_date":active.isoformat(),"home_official":home,"away_official":away,"local_time_text":m.group(1),"kickoff_utc":None,"kickoff_turkey":None,"status":"OFFICIAL_ARTICLE_CANDIDATE_UNVERIFIED_TIME","source_url":URL})
 now=datetime.now(timezone.utc)
 upcoming=[m for m in matches if now.date()<=date.fromisoformat(m["match_date"])<=now.date().fromordinal(now.date().toordinal()+7)]
 report={"source_url":URL,"retrieved_at_utc":now.isoformat(),"parsed_pairs_all_season":len(matches),"upcoming_seven_day_pairs":len(upcoming),"candidates":upcoming,"accepted":False,"reason":"Official article extraction requires fixture identity matching and timezone-safe kickoff validation; not a complete fixture feed"}
 out=Path("data");out.mkdir(exist_ok=True)
 (out/"official_eng1_article_candidates.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"parsed_pairs_all_season":len(matches),"upcoming_seven_day_pairs":len(upcoming),"accepted":False}))
 if not matches:raise SystemExit("Official article did not expose parseable fixtures")
if __name__=="__main__":main()
