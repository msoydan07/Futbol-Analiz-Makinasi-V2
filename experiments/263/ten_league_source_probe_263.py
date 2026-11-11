"""Live, read-only official web-source survey. Zero odds, seals or model writes.

This deliberately does NOT claim a verified user fixture: most examples are
over a week ahead and the model's strict pre-kickoff gate correctly rejects
that. Fetches official domains only. Source blocking is a diagnostic result,
never silently treated as a missing match or a green full-coverage test.
"""
import json,re
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from official_page_lookup_263 import (
    _default_fetch,is_approved_url,parse_official_events)
from iddaa_pdf_team_alias_preflight_263 import LEAGUES,index_registry,resolve_label
from exp_263_batch import clean_rows
from full_match_eligibility_263 import full_match_rows

SOURCES={
    "ENG1":("https://www.premierleague.com/en/news/4725574","epl_nov26_confirmed"),
    "ENG2":("https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/",
            "efl_2026_27_official_tv_selection"),
    "GER1":("https://products.bundesliga.com/fixtures","dfl"),
    "ESP1":("https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-13","jsonld"),
    "ITA1":("https://www.legaseriea.it/serie-a/calendario-risultati","jsonld"),
    "FRA1":("https://ligue1.com/fr/articles/l1_article_5839-","ligue1_2026_round11_tv"),
    "NED1":("https://www.knvb.nl/competities/eredivisie/programma","knvb"),
    "TUR1":("https://www.tff.org/Default.aspx?hafta=12&pageId=198","tff_2026_week12"),
    "POR1":("https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada",
            "ligaportugal_2026_round12_tv"),
    "BEL1":("https://www.proleague.be/jpl-kalender!","belgium_proleague_nextjs_jpl")
}
class Visible(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.skip+=1
        if tag in ("tr","td","div","p","li","h1","h2","h3","h4","br"):self.parts.append(" ")
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript"):self.skip=max(0,self.skip-1)
        if tag in ("tr","td","div","p","li","h1","h2","h3","h4"):self.parts.append(" ")
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
def main():
    index,_,_=index_registry()
    league_rows=defaultdict(list)
    history=clean_rows("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
    for r in history:league_rows[r["league"]].append(r)
    report={}
    for league in LEAGUES:
        url,parser=SOURCES[league]
        eligible,_,_=full_match_rows(league_rows[league])
        latest=max((row["match_date"] for row in eligible),default=None)
        item={"source_url":url,"parser":parser,
              "latest_eligible_match":latest,
              "age_on_nov21":(datetime(2026,11,21).date()-datetime.fromisoformat(latest).date()).days if latest else None,
              "status":"BLOCKED_UNCHECKED","events_total":0,"events_nov20_30":0,
              "canonical_nov20_30":0,"sample":[],"raw_context":""}
        if not is_approved_url(url,league):
            item["status"]="BLOCKED_DOMAIN_NOT_APPROVED";report[league]=item;continue
        try:
            effective,html=_default_fetch(url,league)
            events=parse_official_events(league,html,parser=parser)
            future=[e for e in events if "2026-11-20"<=e["match_date"]<="2026-11-30" and e["kickoff_utc"]]
            canonical=[e for e in future if resolve_label(league,e["home"],index)["status"]=="MAPPED" and
                       resolve_label(league,e["away"],index)["status"]=="MAPPED"]
            item.update(status="OFFICIAL_HTML_FETCHED" if future else "BLOCKED_NO_TIMED_EVENTS",
                        fetched_url=effective,html_bytes=len(html.encode("utf-8")),
                        events_total=len(events),events_nov20_30=len(future),
                        canonical_nov20_30=len(canonical),
                        sample=[{k:e[k] for k in ("home","away","kickoff_utc")} for e in future[:2]])
            if not future:
                v=Visible();v.feed(html)
                raw=re.sub(r"\s+"," ","".join(v.parts)).strip()
                for key in ("21.11.2026","21 nov","21 November","22 November","21 novembro","21 november","JORNADA 13","MATCHDAY 12"):
                    idx=raw.lower().find(key.lower())
                    if idx>=0:
                        item["raw_context"]=raw[max(0,idx-55):idx+220];break
                if not item["raw_context"]:item["raw_context"]=raw[:240]
        except Exception as exc:
            item["status"]="BLOCKED_FETCH_OR_PARSER_ERROR"
            item["error"]=type(exc).__name__+":"+str(exc)[:110]
        report[league]=item
        print("LIVE_10LEAGUE_PROBE="+json.dumps({"league":league,**item},ensure_ascii=False),flush=True)
    result={"schema":"263_READ_ONLY_LIVE_POSTBREAK_TEN_SOURCE_PROBE_V1",
            "day":"2026-11-11","no_predictions":True,"no_bookmakers":True,
            "not_full_user_pdf_acceptance":True,"leagues":report}
    print("LIVE_10LEAGUE_AGGREGATE="+json.dumps({
        "live_fetched":sum(r["status"]=="OFFICIAL_HTML_FETCHED" for r in report.values()),
        "timed_events":sum(r["events_nov20_30"] for r in report.values()),
        "canonical_timed_events":sum(r["canonical_nov20_30"] for r in report.values()),
        "blocked":[l for l,r in report.items() if r["status"]!="OFFICIAL_HTML_FETCHED"]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":main()
