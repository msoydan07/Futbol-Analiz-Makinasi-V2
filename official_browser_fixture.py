"""Browser-rendered official fixtures for sites whose server HTML omits match data.
Fail closed: both teams, date, kickoff and league context must be present.
"""
import json,re,sys,unicodedata
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

SOURCES={
 "BEL1":"https://www.proleague.be/fr/jpl-calendar",
 "POR1":"https://www.ligaportugal.pt/team/176/estoril-praia",
 "ENG2":"https://www.efl.com/news/2026/october/29/referee-appointments--30-october-4-november/",
}
def norm(s):
 s=unicodedata.normalize("NFKD",s.casefold())
 return "".join(c for c in s if c.isalnum() and not unicodedata.combining(c))
def extract(league,lines,home,away,now):
 matches=[]
 if league=="BEL1":
  # Official Pro League calendar cards: home / local? display kickoff / day / away.
  # Pro League website lists kickoffs in UTC (verified against match detail).
  datepat=re.compile(r"^(?:lun|mar|mer|jeu|ven|sam|dim)\.\s*(\d{1,2})\s+(oct|nov)\.$",re.I)
  for i,x in enumerate(lines):
   if norm(x)!=norm(home):continue
   for j in range(i+1,min(i+7,len(lines)-1)):
    if not re.fullmatch(r"\d{1,2}:\d{2}",lines[j]):continue
    for k in range(j+1,min(j+5,len(lines)-1)):
     m=datepat.fullmatch(lines[k])
     if m and any(norm(y)==norm(away) for y in lines[k+1:k+5]):
      d=datetime(now.year,10 if m.group(2).lower()=="oct" else 11,int(m.group(1)),*map(int,lines[j].split(":")),tzinfo=timezone.utc)
      matches.append(d)
 elif league=="POR1":
  # Official Estoril team fixture card: date, J10, FCP, kickoff, EPF.
  if norm(home)=="fcporto" and norm(away)=="estorilpraia":
   for i,x in enumerate(lines):
    if not re.search(r"(?:sáb\.?|sab\.?|sábado)\s*31\s*out",x,re.I):continue
    context=" ".join(lines[i:i+16])
    if re.search(r"\bFCP\b\s+20h30\s+\bEPF\b",context,re.I):
     matches.append(datetime(now.year,10,31,20,30,tzinfo=ZoneInfo("Europe/Lisbon")).astimezone(timezone.utc))
 elif league=="ENG2":
  datepat=re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+(October|November)$",re.I)
  matchpat=re.compile(r"^(.+?)\s+v\s+(.+?)\s+\((\d{1,2}:\d{2})\)$",re.I)
  date=None;champ=False
  for line in lines:
   d=datepat.fullmatch(line)
   if d:
    date=datetime.strptime(f"{d.group(2)} {d.group(3)} {now.year}","%d %B %Y").date()
    champ=False
    continue
   if line.strip().lower() in ("efl championship","sky bet championship"):champ=True;continue
   if re.match(r"^(?:Sky Bet League|EFL League|Jersey Mike)",line,re.I):champ=False
   m=matchpat.fullmatch(line)
   if date and champ and m and norm(m.group(1))==norm(home) and norm(m.group(2))==norm(away):
    local=datetime.strptime(str(date)+" "+m.group(3),"%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/London"))
    matches.append(local.astimezone(timezone.utc))
 return sorted(set(matches))
def lookup(league,home,away):
 now=datetime.now(timezone.utc);url=SOURCES[league]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
   page=browser.new_page(locale="en-GB",timezone_id="Europe/London",user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36")
   page.goto(url,wait_until="domcontentloaded",timeout=25000)
   page.wait_for_timeout(5000)
   body=page.locator("body").inner_text(timeout=10000)
   browser.close()
 except Exception as e:
  return {"status":"NOT_VERIFIED","reason":"browser_fetch_failed","detail":str(e)[:240],"source_url":url}
 lines=[x.strip() for x in body.splitlines() if x.strip()]
 hits=extract(league,lines,home,away,now)
 if len(hits)!=1:
  terms=[norm(home),norm(away),"fcp","epf","blackburn","stoke","mechelen","genk"]
  samples=[lines[max(0,i-3):i+7] for i,x in enumerate(lines) if any(t in norm(x) for t in terms)][:6]
  return {"status":"NOT_VERIFIED","reason":"fixture_not_unique","count":len(hits),"lines_seen":len(lines),"samples":samples,"source_url":url}
 kick=hits[0]
 if not now<=kick<=now+timedelta(days=7):
  return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat(),"source_url":url}
 return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":url,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING"}
if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2],sys.argv[3]);print(json.dumps(r,ensure_ascii=False,indent=2))
 sys.exit(0 if r["status"]=="VERIFIED_OFFICIAL_FIXTURE" else 1)
