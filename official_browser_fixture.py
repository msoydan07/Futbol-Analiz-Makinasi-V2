"""Browser-rendered official fixtures for sites whose server HTML omits match data.
Fail closed: both teams, date, kickoff and league context must be present.
"""
import json,re,sys,unicodedata
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo

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
  # Official club calendar table rows: local time and both teams in one row.
  club_re=re.compile(r"^(?:za|zo|ma|di|wo|do|vr)\s+(\d{1,2})\s+(okt|nov|dec)\s*[-–]\s*(\d{1,2}):(\d{2})\s+(.+?)\s+(.+)$",re.I)
  for line in lines:
   m=club_re.fullmatch(line)
   if m and norm(m.group(5))==norm(home) and norm(m.group(6))==norm(away):
    local=datetime(now.year,{"okt":10,"nov":11,"dec":12}[m.group(2).lower()],int(m.group(1)),int(m.group(3)),int(m.group(4)),tzinfo=ZoneInfo("Europe/Brussels"))
    matches.append(local.astimezone(timezone.utc))
  # Official Pro League calendar cards: home / local? display kickoff / day / away.
  # Pro League website lists kickoffs in UTC (verified against match detail).
  datepat=re.compile(r"^(?:lun|mar|mer|jeu|ven|sam|dim|ma|di|wo|do|vr|za|zo)\.\s*(\d{1,2})\s+(oct|nov|okt)\.$",re.I)
  for i,x in enumerate(lines):
   if norm(x)!=norm(home):continue
   for j in range(i+1,min(i+7,len(lines)-1)):
    if not re.fullmatch(r"\d{1,2}:\d{2}",lines[j]):continue
    for k in range(j+1,min(j+5,len(lines)-1)):
     m=datepat.fullmatch(lines[k])
     if m and any(norm(y)==norm(away) for y in lines[k+1:k+5]):
      d=datetime(now.year,10 if m.group(2).lower() in ("oct","okt") else 11,int(m.group(1)),*map(int,lines[j].split(":")),tzinfo=timezone.utc)
      matches.append(d)
 elif league=="POR1":
  # Parse visible match cards, not a particular club or a fixed date.
  # Cards expose e.g. "sáb. 31 out", "FCP", "20h30", "EPF".
  # Abbreviations are accepted only for a known exact team identity.
  # Exact aliases only: never guess an abbreviation from a team name.
  aliases={
   "fcporto":{"fcp","fcporto"},
   "estorilpraia":{"epf","estorilpraia"},
  }
  h=aliases.get(norm(home),{norm(home)})
  a=aliases.get(norm(away),{norm(away)})
  if h & a:
   return []
  months={"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}
  dp=re.compile(r"(?:seg|ter|qua|qui|sex|s[aá]b|dom)\.?\s*(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\b",re.I)
  tp=re.compile(r"\b(\d{1,2})h(\d{2})\b",re.I)
  for i,line in enumerate(lines):
   dm=dp.search(line)
   if not dm:continue
   # Do not borrow a kickoff or team from the following match-day card.
   next_day=next((k for k in range(i+1,len(lines)) if dp.search(lines[k])),len(lines))
   context=lines[i+1:min(i+17,next_day)]
   for j,x in enumerate(context):
    if norm(x) not in h:continue
    for k in range(j+1,min(j+7,len(context))):
     tm=tp.fullmatch(context[k])
     if not tm:continue
     if any(norm(y) in a for y in context[k+1:k+5]):
      year=now.year+(1 if now.month==12 and months[dm.group(2).lower()]<=2 else 0)
      local=datetime(year,months[dm.group(2).lower()],int(dm.group(1)),int(tm.group(1)),int(tm.group(2)),tzinfo=ZoneInfo("Europe/Lisbon"))
      matches.append(local.astimezone(timezone.utc))
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
FALLBACK_SOURCES={"BEL1":["https://kvmechelen.be/kalenderupdatesept/","https://www.krcgenk.be/en","https://www.proleague.be/nl/jpl-calendar"]}
def lookup(league,home,away):
 from playwright.sync_api import sync_playwright
 now=datetime.now(timezone.utc);url=SOURCES[league]
 attempts=[]
 for candidate in [url]+FALLBACK_SOURCES.get(league,[]):
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    try:
     page=browser.new_page(locale="fr-BE" if league=="BEL1" else "en-GB")
     response=page.goto(candidate,wait_until="domcontentloaded",timeout=20000)
     status=response.status if response else None
     body=""
     if status==200:
      page.wait_for_timeout(3500)
      body=page.locator("body").inner_text(timeout=10000)
     lines=[x.strip() for x in body.splitlines() if x.strip()]
     hits=extract(league,lines,home,away,now) if status==200 else []
     attempts.append({"url":candidate,"http_status":status,"visible_chars":len(body),"matches":len(hits)})
     if len(hits)!=1:continue
     kick=hits[0]
     if not now<=kick<=now+timedelta(days=7):
      return {"status":"OUTSIDE_WINDOW","kickoff_utc":kick.isoformat(),"source_url":candidate,"attempts":attempts}
     return {"status":"VERIFIED_OFFICIAL_FIXTURE","home":home,"away":away,"kickoff_utc":kick.isoformat(),"source_url":candidate,"retrieved_at_utc":now.isoformat(),"identity_match":"PENDING","attempts":attempts}
    finally:
     browser.close()
  except Exception as e:
   attempts.append({"url":candidate,"error":str(e)[:120]})
 return {"status":"NOT_VERIFIED","reason":"no_unique_fixture_in_official_sources","attempts":attempts}

if __name__=="__main__":
 r=lookup(sys.argv[1],sys.argv[2],sys.argv[3]);print(json.dumps(r,ensure_ascii=False,indent=2))
 sys.exit(0 if r["status"]=="VERIFIED_OFFICIAL_FIXTURE" else 1)
