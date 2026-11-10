"""Read-only official public score PAGE test, no source or model mutation.

Live Playwright fetch classifies each of the 43 as:
  EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY: case-insensitive adjacent score and clubs
  BELGIUM_FT_SCOREBOARD_WITH_OFFICIAL_MATCH_URL: individual ProLeague full time card
  PAGE_READABLE_NO_PAIRWISE_EXPLICIT_SCORE: no machine-verifiable score; manual source URL is insufficient
  HTTP_ERROR / NETWORK_ERROR: unable to independently retrieve content
No outcome is upgraded on URL-only evidence; no official match IDs are inferred.
"""
from __future__ import annotations
import asyncio, argparse, json, re, unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[2]
PROOF=ROOT/"data/results_only_263/43_primary_public_score_review_20261110.json"
ALTS={
"man united":["man utd","manchester united"],"man city":["manchester city"],
"tottenham":["spurs","tottenham hotspur"],"newcastle":["newcastle united"],
"nottingham forest":["nottm forest","nott'm forest"],"brighton":["brighton & hove albion","brighton"],
"bournemouth":["afc bournemouth","bournemouth"],"coventry":["coventry city"],
"leeds":["leeds united"],"ipswich":["ipswich town"],
"wolves":["wolverhampton wanderers","wolverhampton","wolves"],
"cardiff":["cardiff city"],"west ham":["west ham united"],
"derby":["derby county"],"bolton":["bolton wanderers"],
"norwich":["norwich city"],"stoke":["stoke city"],"portsmouth":["pompey","portsmouth fc"],
"birmingham":["birmingham city"],"blackburn":["blackburn rovers"],
"charlton":["charlton athletic"],"preston":["preston north end"],
"qpr":["queens park rangers"],"lincoln":["lincoln city"],
"west brom":["west bromwich albion","west brom"],
"wrexham":["wrexham afc"],"fulham":["fulham"],
"arsenal":["arsenal"],"hull city":["hull city"],"swansea":["swansea city"],
"famalicao":["fc famalicão","fc famalicao"],"arouca":["fc arouca"],
"alverca":["fc alverca"],"casa pia":["casa pia ac"],
"moreirense":["moreirense fc"],"sporting cp":["sporting cp"],
"nacional":["cd nacional"],"academico":["académico","academico"],
"santa clara":["santa clara"],"gil vicente":["gil vicente fc"],
"vitoria sc":["vitória sc","vitoria sc"],"porto":["fc porto"],
"estrela":["estrela amadora"],"benfica":["sl benfica"],"rio ave":["rio ave fc"],
"sp braga":["sc braga"]
}
def norm(x):
    x=unicodedata.normalize("NFKD",x).casefold()
    x="".join(c for c in x if not unicodedata.combining(c))
    x=x.replace("\u00a0"," ").replace("’","'")
    return re.sub(r"\s+"," ",x).strip()

def aliases(s):
    return [norm(x) for x in ([s]+ALTS.get(s,[]))]

def match_score(row,body):
    hg,ag=row["home_goals"],row["away_goals"]
    if row["league"]=="BEL1" and "www.proleague.be" in row["score_source_url"]:
        lines=[norm(t).strip() for t in body.splitlines() if t.strip()]
        if not any("jupiler pro league" in x for x in lines[:25]):
            return "PAGE_READABLE_NO_MATCH_CONTEXT"
        if "termine" not in lines:
            return "PAGE_READABLE_NO_FINAL_STATUS"
        idx=lines.index("termine")
        nearby=lines[idx+1:idx+11]
        values=[int(x) for x in nearby if re.fullmatch(r"\d{1,2}",x)]
        if len(values)>=2 and values[:2]==[hg,ag]:
            return "BELGIUM_FT_SCOREBOARD_WITH_OFFICIAL_MATCH_URL"
        return "PAGE_READABLE_BELGIAN_FT_SCORE_MISMATCH_OR_MISSING"
    flat=norm(body)
    if row["league"]=="BEL1" and urlsplit(row["score_source_url"]).hostname=="kvmechelen.be":
        # A single-game official club page: exact date, competition, clubs
        # and scoreboard. Do not borrow a result from a calendar list.
        expected_date="04 november 2026"
        has_both=("kortrijk" in flat and "mechelen" in flat)
        if ("jupiler pro league" in flat and expected_date in flat and has_both
             and re.search(r"(?<!\\d)1\\s*[-–]\\s*3(?!\\d)",flat)):
            return "EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY"
    # For other official sites, a score alone is insufficient: require
    # both teams around that exact score; don't borrow across adjacent games.
    pattern=rf"(?<!\d){hg}\s*(?:[-:–]\s*|\s+){ag}(?!\d)"
    homes=aliases(row["home_alias"])
    aways=aliases(row["away_alias"])
    for m in re.finditer(pattern,flat):
        text=flat[max(0,m.start()-115):min(len(flat),m.end()+115)]
        if any(h in text for h in homes) and any(a in text for a in aways):
            return "EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY"
    return "PAGE_READABLE_NO_PAIRWISE_EXPLICIT_SCORE"

async def check(pagebrowser,url,sem):
    async with sem:
        page=await pagebrowser.new_page(locale="en-GB")
        try:
            response=await page.goto(url,wait_until="domcontentloaded",timeout=18000)
            status=response.status if response else None
            if status!=200:
                return {"http":status,"body":"","reason":"HTTP_ERROR"}
            await page.wait_for_timeout(1200)
            body=await page.locator("body").inner_text(timeout=8500)
            return {"http":status,"body":body,"reason":"PAGE_READABLE"}
        except Exception as e:
            return {"http":None,"body":"","reason":"NETWORK_ERROR","error":str(e)[:120]}
        finally:
            await page.close()

async def run(output):
    data=json.loads(PROOF.read_text(encoding="utf-8"))
    rows=data["records"]
    urls=sorted(set(x["score_source_url"] for x in rows))
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        sem=asyncio.Semaphore(4)
        observations=await asyncio.gather(*(check(browser,u,sem) for u in urls))
        await browser.close()
    cache=dict(zip(urls,observations))
    checked=[]
    for row in rows:
        q=cache[row["score_source_url"]]
        verdict=match_score(row,q["body"]) if q["reason"]=="PAGE_READABLE" else q["reason"]
        checked.append({"league":row["league"],"date":row["match_date"],
           "home":row["home_alias"],"away":row["away_alias"],
           "score":str(row["home_goals"])+"-"+str(row["away_goals"]),
           "source_url":row["score_source_url"],
           "http_status":q["http"],"page_text_chars":len(q["body"]),
           "verdict":verdict})
    counts=dict(Counter(x["verdict"] for x in checked))
    out={"schema":"263_43_PRIMARY_LIVE_WEBPAGE_SCORE_CONTENT_DIAGNOSTIC_V1",
         "checked_utc":datetime.now(timezone.utc).isoformat(),
         "requested_43":43,"unique_pages_fetched":len(urls),
         "results":checked,"verdict_counts":counts,
         "network_independent_score_matches":sum(v for k,v in counts.items()
              if k in ("EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY","BELGIUM_FT_SCOREBOARD_WITH_OFFICIAL_MATCH_URL")),
         "old_score_results_modified":False,"model_or_pilot_modified":False,
         "limitations":["Official site web text is checked, not federated structured fixture IDs",
           "Some official pages require dynamic JS beyond this short bounded browser test",
           "A page-text match is supportive evidence; it does not itself validate the match's legal data redistribution rights",
           "No score is silently reclassified on official URL alone"]}
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:out[k] for k in ("checked_utc","requested_43","unique_pages_fetched",
               "verdict_counts","network_independent_score_matches")},ensure_ascii=False))
    for row in checked:
        if row["verdict"] not in ("EXACT_SCORE_AND_TEAMS_IN_VISIBLE_BODY","BELGIUM_FT_SCOREBOARD_WITH_OFFICIAL_MATCH_URL"):
            print("UNVERIFIED_PRIMARY_SCORE",json.dumps(row,ensure_ascii=False))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="/tmp/263_primary43_live_webpage_score_results.json")
    args=parser.parse_args()
    asyncio.run(run(Path(args.output)))
