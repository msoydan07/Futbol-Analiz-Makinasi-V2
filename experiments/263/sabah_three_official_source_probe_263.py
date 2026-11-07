"""No-odds live diagnostics of three official football fixtures sources.

Never selects a game, creates predictions, changes pilot counts or claims
live fixture completeness. Only outputs small sanitized source signatures.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from official_page_lookup_263 import _default_fetch,is_approved_url,_Markup,parse_official_events

CANDIDATES={
 "ENG2":[
   "https://www.efl.com/",
   "https://www.efl.com/match-centre/g2647481",
   "https://www.efl.com/news/2026/november/06/how-to-watch-and-follow-the-sky-bet-championship-this-weekend/"],
 "POR1":[
   "https://www.ligaportugal.pt/calendar",
   "https://www.ligaportugal.pt/news/29039/media-kits-jornada-11-da-liga-portugal-betclic",
   "https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada"],
 "BEL1":[
   "https://www.proleague.be/jpl-kalender!",
   "https://www.proleague.be/wedstrijden/seizoen-2026-2027-jupiler-pro-league-11-royale-union-saint-gilloise-vs-krc-genk-693"]
}
PHRASES={"ENG2":("wrexham","bristol","championship","november","2026-11-07"),
         "POR1":("sporting","moreirense","novembro","2026-11-08","portugal"),
         "BEL1":("westerlo","club brugge","nov","rsc anderlecht","november")}
class Images(HTMLParser):
    def __init__(self):
        super().__init__();self.alt=[]
    def handle_starttag(self,tag,attrs):
        if tag!="img":return
        a=dict(attrs).get("alt","")
        if len(a)>2 and a not in self.alt and len(self.alt)<100:self.alt.append(a)
def signature(league,url,fetcher=_default_fetch):
    if league not in CANDIDATES or url not in CANDIDATES[league] or not is_approved_url(url,league):
        raise ValueError("NOT_PREAPPROVED_OFFICIAL_SOURCE")
    result={"league":league,"requested_url":url,"status":"SOURCE_BLOCKED","no_pilot_record":True}
    try:
        final,html=fetcher(url,league)
        if not is_approved_url(final,league):raise ValueError("OFFICIAL_REDIRECT_UNTRUSTED")
        # Public official HTML used only to inspect exact BEL1 card time fields.
        # Diagnostic artifact, never fixture acceptance or a bookmaker quote.
        if league=="BEL1" and url==CANDIDATES["BEL1"][0]:
            Path("/tmp/263-proleague-official-raw.html").write_text(html,encoding="utf-8")
        m=_Markup();m.feed(html);imgs=Images();imgs.feed(html)
        excerpts=[]
        for term in PHRASES[league]:
            match=re.search(re.escape(term),html,re.IGNORECASE)
            if match:
                excerpts.append({"term":term,"sample":html[max(0,match.start()-175):match.end()+300]})
        # Small raw blocks strictly for official HTML parser development.
        detail=""
        if league=="BEL1":
            q=re.search(r'<article[^>]+MkFootballMatchCard[^>]+aria-label="[^"]+"',html,re.I)
            if q:detail=html[q.start():q.start()+4400]
        elif league=="POR1":
            q=re.search(r'(?:Sexta-feira, 6 de novembro|Domingo, 8 de novembro)',html,re.I)
            if q:detail=html[max(0,q.start()-200):q.start()+4200]
        elif league=="ENG2":
            q=re.search(r'(?:Wrexham|Bristol City|Championship)',html,re.I)
            if q:detail=html[max(0,q.start()-200):q.start()+1500]
        visible=" ".join("".join(m.visible).split())
        found=parse_official_events(league,html,parser="jsonld")
        result.update(status="FETCHED_OFFICIAL_HTML",
                      effective_url=final,
                      html_length=len(html),
                      sha256=hashlib.sha256(html.encode("utf-8")).hexdigest(),
                      jsonld_sportsevents=len(found),
                      jsonld_script_tags=len(m.jsonld),
                      relevant_html_excerpts=excerpts,
                      visible_size=len(visible),
                      visible_sample=visible[:900],
                      image_alts=imgs.alt[:40],
                      title_sample=html[:350],
                      response_lacks_usable_timed_structure=len(found)==0,
                      official_parser_detail=detail)
    except (OSError,ValueError,TypeError,TimeoutError,UnicodeError) as e:
        result["reason"]=type(e).__name__+":"+str(e)[:120]
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);args=p.parse_args()
    out={"schema":"263_THREE_OFFICIAL_SOURCE_FORMAT_DIAGNOSTIC_V1",
         "checked_at_utc":datetime.now(timezone.utc).isoformat(),
         "calls_for_odds":0,"new_pilot_records":0,
         "can_directly_promote_to_pilot":False,
         "sources":[signature(league,url) for league,urls in CANDIDATES.items() for url in urls]}
    file=Path(args.out);file.parent.mkdir(parents=True,exist_ok=True)
    with file.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
    print(json.dumps({x["requested_url"]:x.get("status")+":LD="+str(x.get("jsonld_sportsevents"))
                       for x in out["sources"]},ensure_ascii=False))
if __name__=="__main__":main()
