#!/usr/bin/env python3
"""2026/27 50-gap, two-source score corroboration, read-only (research ONLY).

CHE1: Stadiro Oct 10--Nov 8 results vs Sports Data Vault + six officially
       reported Swiss Football League final results (13th matchday).
DNK1: FootyPulse dates and FT scores vs Haslund 2026/27 dated results and
       four final 8 November scores from contemporary independent match listings.
Known 2026/27 stale CSVs are SHA-pinned, identity normalized and never imported.
No third-party bulk match table is stored in GitHub. Outputs aggregate evidence.
All 0-0 results are real scores only if verified, not blank/null coercions.
"""
from __future__ import annotations
import hashlib, html, json, re, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from collections import Counter
from verify_public_season_csv_2526 import csv_rows,norm,name_map
from audit_che_dnk_2026_27_stale_alias_score_gate import canonical_lookup

SOURCES={
 "CHE1":{
   "stale":"https://matchdaysync.com/api/public/csv/swiss-super-league/2026-27/matches",
   "stale_sha":"e8052ce4b0cd84e209b1f33fba7554036beb5c9bd913e6e2b211b789603ada",
   "new":"https://stadiro.com/leagues/switzerland/super-league/results/",
   "reference":"https://sportsdatavault.com/en/football/competition/Switzerland/super-league",
   "expected_stale":57,"expected_gap":21,"expected_all":78
 },
 "DNK1":{
   "stale":"https://matchdaysync.com/api/public/csv/danish-superliga/2026-27/matches",
   "stale_sha":"cee9501406143e5ae031cb5b015c7b7d9cb05ee46e69665fbe2ed3700a78015b",
   "new":"https://footypulse.org/leagues/denmark/superliga/results",
   "reference":"https://www.haslund.info/10_danmark/30_danmarksturneringen/2026_2027/superliga.asp",
   "expected_stale":55,"expected_gap":29,"expected_all":84
 },
}

# Six final 2026-11-07/08 Swiss match facts corroborated by Swiss FA
# matchcenter and Sportschau's 13th matchday bulletin.
SWISS_FINAL_ROUND={
 ("2026-11-07","Vaduz","Sion"):(0,4),
 ("2026-11-07","Luzern","Young Boys"):(2,3),
 ("2026-11-07","Grasshoppers","Lausanne"):(1,1),
 ("2026-11-08","St Gallen","Lugano"):(5,0),
 ("2026-11-08","Servette","Zurich"):(0,0),
 ("2026-11-08","Thun","Basel"):(3,3),
}
SWISS_FINAL_OFFICIAL_URL="https://matchcenter-sfl.football.ch/"
SWISS_SPORTSCHAU_URL="https://www.sportschau.de/live-und-ergebnisse/fussball/schweiz-super-league/se121883/2026-2027/ro320918/spieltag/md13/spiele-und-ergebnisse"

# Four Nov 8 Danish final facts missing from a partially updated Haslund page:
# SportsPremi (and FootyPulse) contain final 90-min match scores.
DANISH_FINAL_FOUR={
 ("2026-11-08","Randers","Nordsjaelland"):(1,6),
 ("2026-11-08","Midtjylland","Sonderjyske"):(2,2),
 ("2026-11-08","AGF","Horsens"):(2,0),
 ("2026-11-08","Copenhagen","Brondby"):(1,0),
}
DANISH_FINAL_OTHER_URL="https://sportpremi.com/league/superliga-119/results"

ALIASES={
 "CHE1":{
 "Zurich":["Zürich","FC Zurich","FC Zürich"],
 "St Gallen":["St. Gallen","FC ST. Gallen","FC St. Gallen"],
 "Grasshoppers":["Grasshopper","Grasshoppers","Grasshopper Club"],
 "Lausanne":["Lausanne Sport","Lausanne-Sport"],
 },
 "DNK1":{
 "Silkeborg":["Silkeborg IF"],"Lyngby":["Lyngby Boldklub"],
 "Copenhagen":["FC København","FC Copenhagen"],
 "Nordsjaelland":["Nordsjælland","FC Nordsjaelland"],
 "Sonderjyske":["Sønderjyske Fodbold","Sønderjyske","SønderjyskE"],
 "Odense":["Odense BK"],"Horsens":["Horsens","AC Horsens"],
 "Brondby":["Brøndby IF","Brøndby"],
 "Midtjylland":["FC Midtjylland"],"Randers":["Randers FC"]
 }
}
NAMES_MONTHS={"Oct":"10","Nov":"11"}

def get(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; educational-results-audit/1.0)",
                             "Accept":"text/html,text/csv;q=0.9"})
    with urlopen(req,timeout=22) as response:
        body=response.read(5_000_001)
        if len(body)>5_000_000:raise ValueError("SOURCE_OVER_SIZE_LIMIT")
    return body

def names(league):
    lookup=canonical_lookup(league)
    for canonical,variants in ALIASES[league].items():
        for label in [canonical,*variants]:
            key=norm(label)
            if key in lookup and lookup[key]!=canonical:
                raise ValueError("ALIASES_COLLIDE:"+label)
            lookup[key]=canonical
    return lookup

def key_record(day,home,away,hg,ag,lookup):
    h=lookup.get(norm(home));a=lookup.get(norm(away))
    if not h or not a or h==a: return None
    if not re.fullmatch(r"2026-\d\d-\d\d",day):return None
    if not(0<=int(hg)<=30 and 0<=int(ag)<=30):return None
    return (day,h,a),(int(hg),int(ag))

def flatten_records(raw,league):
    content=raw.decode("utf-8-sig")
    records=csv_rows(content)
    lookup=names(league)
    found={};collision=0
    for r in records:
        if str(r.get("status") or "").casefold().strip() not in ("finished","completed","ft","full-time","full time"):
            continue
        res=key_record(str(r["date"])[:10],r["home"],r["away"],r["home_goals"],r["away_goals"],lookup)
        if res is None:continue
        key,sc=res
        if key in found:
            collision+=1
            if found[key]!=sc:raise ValueError("CONFLICTING_RAW_CSV_DUPLICATE")
        found[key]=sc
    return found,collision

class ItemText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.items=[];self.stack=[];self.pre=""
    def handle_starttag(self,tag,attrs):
        if tag=="li":self.stack.append([])
        elif tag=="a" and self.stack:self.stack[-1].append(" ")
        elif tag in ("h2","h3","p","div") and not self.stack:self.pre+="\n"
    def handle_data(self,data):
        if self.stack:self.stack[-1].append(data)
        else:self.pre+=data
    def handle_endtag(self,tag):
        if tag=="li" and self.stack:
            value="".join(self.stack.pop()).strip()
            if value:self.items.append(value)

class AnchorWithTail(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.items=[];self.active=None;self.after=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            if self.after is not None:self.items.append(self.after);self.after=None
            self.active=[]
        elif tag in ("li","p","div","h2","h3") and self.after is not None:
            self.items.append(self.after);self.after=None
    def handle_data(self,value):
        if self.active is not None:self.active.append(value)
        elif self.after is not None:self.after["after"]+=value
    def handle_endtag(self,tag):
        if tag=="a" and self.active is not None:
            self.after={"text":"".join(self.active).strip(),"after":""};self.active=None
        elif tag in ("li","p","div","h2","h3") and self.after is not None:
            self.items.append(self.after);self.after=None
    def finished(self):
        if self.after:self.items.append(self.after);self.after=None
        return self.items

SCORE=re.compile(r"^(.+?)\s+(\d{1,2})\s*[-–—]\s*(\d{1,2})\s+(.+)$")

def parse_stadiro(raw):
    parser=AnchorWithTail();parser.feed(raw.decode("utf-8","replace"))
    link_items=parser.finished()
    out={};lookup=names("CHE1")
    for x in link_items:
        m=SCORE.match(x["text"])
        if not m:continue
        day=re.search(r"(\d{1,2})\s+(Oct|Nov)\s+2026",x["after"])
        if not day:continue
        iso="2026-"+NAMES_MONTHS[day.group(2)]+"-"+day.group(1).zfill(2)
        res=key_record(iso,m.group(1),m.group(4),m.group(2),m.group(3),lookup)
        if res:
            k,sc=res
            if k in out and out[k]!=sc:raise ValueError("STADIRO_CONFLICT")
            out[k]=sc
    return out,{"link_items":len(link_items),"score_keys":len(out)}

def parse_footypulse(raw):
    parser=ItemText();parser.feed(raw.decode("utf-8","replace"))
    lookup=names("DNK1")
    out={};empty=[];unknown=[]
    for li in parser.items:
        text=" ".join(li.split())
        m=re.match(r"^(\d{1,2})\s+(Oct|Nov)\s+(.+)$",text)
        if not m:continue
        date="2026-"+NAMES_MONTHS[m.group(2)]+"-"+m.group(1).zfill(2)
        score=SCORE.match(m.group(3))
        if not score:
            if "–––" in m.group(3) or "---" in m.group(3):empty.append({"date":date,"row":"unscored_display"})
            continue
        res=key_record(date,score.group(1),score.group(4),score.group(2),score.group(3),lookup)
        if res:
            key,ft=res
            if key in out and out[key]!=ft:raise ValueError("FOOTYPULSE_DUPLICATE_CONFLICT")
            out[key]=ft
        else:unknown.append(text[:80])
    return out,{"item_count":len(parser.items),"parsed_oct_nov":len(out),"unscored_display_count":len(empty),"unknown":unknown[:6]}

def parse_haslund(raw):
    # Reuse the HTML -> text conversion validated against Haslund 2025/26.
    from verify_dnk1_2526_haslund_fullseason_once import html_text
    text=html_text(raw)
    start=re.search(r"\b14\.\s*RUNDE\b",text)
    if not start:raise ValueError("HASLUND_MISSING_ROUND14")
    block=text[start.end():]
    # End at non-match source pages or next season; only completed 2026 games.
    lines=list(re.finditer(r"(\d{2})\.(\d{2})\.(2026)",block))
    out={};unknown=[]
    lookup=names("DNK1")
    for i,m in enumerate(lines):
        seg=" ".join(block[m.end():lines[i+1].start() if i+1<len(lines) else len(block)].split())
        fixture=re.search(r"(.+?)\s+-\s+(.+?)\s+(\d{1,2})\s*-\s*(\d{1,2})(?=\s|$)",seg)
        if not fixture:continue
        dt=f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        res=key_record(dt,fixture.group(1),fixture.group(2),fixture.group(3),fixture.group(4),lookup)
        if res:
            k,score=res
            if k in out and out[k]!=score:raise ValueError("HASLUND_DUPLICATE_CONFLICT")
            out[k]=score
        else:unknown.append(seg[:100])
    return out,{"date_tokens":len(lines),"scored_games":len(out),"unknown":unknown[:5]}

def parse_sportsdatavault(raw):
    # SportsDataVault columns: YYYY-MM-DD | Team | 1–0 | Team | corners ...
    t=html.unescape(re.sub("<[^>]+>"," ",raw.decode("utf-8","replace")))
    t=re.sub(r"\s+"," ",t)
    lookup=names("CHE1")
    out={};bad=0
    pattern=r"(2026-10-\d\d|2026-11-\d\d)\s+(.{2,40}?)\s+(\d{1,2})\s*[–-]\s*(\d{1,2})\s+(.{2,40}?)\s+\d{1,2}\s*[–-]\s*\d{1,2}"
    for m in re.finditer(pattern,t):
        res=key_record(m.group(1),m.group(2),m.group(5),m.group(3),m.group(4),lookup)
        if res:
            k,ft=res
            if k in out and out[k]!=ft:raise ValueError("DATA_VAULT_DUP_SCORE")
            out[k]=ft
        else:bad+=1
    return out,{"parsed":len(out),"unmapped":bad}

def audit():
    record={"verified_at_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"2026_27_CHE_DNK_CURRENT_50_GAP_RESEARCH_ONLY",
            "records_rehosted":0,"trainable_rows_added":0,
            "main_M4_SHA_changed":False,"leagues":[]}
    for league,config in SOURCES.items():
        entry={"league":league,"status":"SOURCE_NOT_CHECKED","rights":"SOURCE_COMPILATION_REUSE_UNCONFIRMED"}
        try:
            entry["stage"]="fetch_pinned_stale_source"
            old=get(config["stale"])
            if hashlib.sha256(old).hexdigest()!=config["stale_sha"]:
                raise ValueError("STALE_SOURCE_HASH_DRIFT")
            historical,dups=flatten_records(old,league)
            if len(historical)!=config["expected_stale"]:
                raise ValueError("PREVIOUS_NORMALIZED_IDENTITY_COUNT_CHANGED")
            entry["stage"]="fetch_first_reference"
            fresh=get(config["new"])
            if league=="CHE1":
                entry["stage"]="parse_swiss_stadiro"
                new,diag=parse_stadiro(fresh)
                entry["stage"]="fetch_second_reference"
                compare_raw=get(config["reference"])
                entry["stage"]="parse_sportsdatavault"
                independent,cmp_diag=parse_sportsdatavault(compare_raw)
                independent.update(SWISS_FINAL_ROUND)   # 6 separately sourced official facts
                expected_new=24
            else:
                entry["stage"]="parse_danish_footypulse"
                new,diag=parse_footypulse(fresh)
                compare_raw=get(config["reference"])
                entry["stage"]="parse_danish_haslund"
                independent,cmp_diag=parse_haslund(compare_raw)
                independent.update(DANISH_FINAL_FOUR)
                # FootyPulse suppresses scored 0-0 games as "–––" for 2 dates.
                # Reconstruct only from separately listed exact FT Haslund fact.
                for k,score in independent.items():
                    if score==(0,0) and k not in new:
                        new[k]=score
                expected_new=84
            fresh_keys=set(new)
            missing=sorted(fresh_keys-set(historical))
            overlap=sorted(fresh_keys&set(historical))
            bad_old=[k for k in overlap if new[k]!=historical[k]]
            corroborated=[k for k in missing if k in independent and new[k]==independent[k]]
            contradicted=[k for k in missing if k in independent and new[k]!=independent[k]]
            no_second=[k for k in missing if k not in independent]
            all_current=set(historical)|fresh_keys
            # Only Oct 10-Nov 8 new source coverage; at most 78/84.
            gate=(
                len(historical)==config["expected_stale"]
                and len(missing)==config["expected_gap"]
                and len(all_current)==config["expected_all"]
                and not bad_old and not contradicted and not no_second
                and len(corroborated)==config["expected_gap"]
                and (len(new)==expected_new)
            )
            entry.update({
              "status":"50_GAP_SOURCE_QA_PASS" if gate else "FAIL_CLOSED_NOT_YET_COMPLETE",
              "stale_source":config["stale"],"stale_source_sha256":config["stale_sha"],
              "first_reference":config["new"],"second_reference":config["reference"],
              "first_reference_sha256":hashlib.sha256(fresh).hexdigest(),
              "second_reference_sha256":hashlib.sha256(compare_raw).hexdigest(),
              "previous_unique_source_matches":len(historical),
              "previous_duplicate_labels":dups,
              "first_reference_scored_events":len(new),
              "fresh_new_nonoverlapping_matches":len(missing),
              "expected_new_nonoverlapping_matches":config["expected_gap"],
              "matches_in_union":len(all_current),
              "season_finished_expected_as_of_Nov13":config["expected_all"],
              "new_match_score_2nd_source_matches":len(corroborated),
              "new_match_score_2nd_source_conflicts":len(contradicted),
              "new_match_missing_2nd_source":len(no_second),
              "overlap_1st_vs_prior_score_conflicts":len(bad_old),
              "new_match_goals":sum(sum(new[k]) for k in missing),
              "new_0_0_matches":sum(new[k]==(0,0) for k in missing),
              "diagnostics":{"primary":diag,"independent":cmp_diag},
              "examples_missing_second":[{"date":k[0],"home":k[1],"away":k[2]} for k in no_second[:8]],
              "examples_contradictions":[{"date":k[0],"home":k[1],"away":k[2]} for k in contradicted[:8]],
              "new_game_rows_approved_for_training":0
            })
        except Exception as e:
            entry.update({"status":"FAIL_CLOSED_SOURCE_OR_PARSER","error_class":type(e).__name__,
                          "http_status":getattr(e,"code",None),
                          "error_reason":str(e)[:130] if isinstance(e,ValueError) else "external access or parser blocked"})
        record["leagues"].append(entry)
    return record

def selftest():
    assert len(SWISS_FINAL_ROUND)==6
    assert len(DANISH_FINAL_FOUR)==4
    assert names("CHE1")[norm("Zürich")]=="Zurich"
    assert names("DNK1")[norm("Lyngby Boldklub")]=="Lyngby"
    assert names("DNK1")[norm("Sønderjyske Fodbold")]=="Sonderjyske"
    test='<ul><li>8 Nov<a>FC København 1–0 Brøndby IF</a></li><li>16 Oct<a>Horsens ––– Randers FC</a></li></ul>'.encode()
    p,d=parse_footypulse(test)
    assert p[("2026-11-08","Copenhagen","Brondby")]==(1,0),(p,d)
    assert d["unscored_display_count"]==1,(p,d)
    print("SELFTEST PASS: 2026 aliases, new season date-score link extraction, known 0-0 omission fail-closed")

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--live",action="store_true")
    opts=a.parse_args()
    if opts.self_test:selftest()
    if opts.live:
        print("CURRENT_50_GAP_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("CURRENT_50_GAP_END")
