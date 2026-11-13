#!/usr/bin/env python3
"""One-time independent Danish Superliga 2025/26 fixture-score reconciliation.

Haslund rounds: regular 22 x 6, championship 10 x 3, relegation 10 x 3.
Two missing championship score entries are corroborated by independent club
and match reports. Public primary CSV pinned by SHA, kept only in memory.
No raw season feeds copied, no training, and no production modifications.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone, date
from html.parser import HTMLParser
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from verify_public_season_csv_2526 import name_map, norm, csv_rows

PRIMARY = "https://matchdaysync.com/api/public/csv/danish-superliga/2025-26/matches"
PRIMARY_SHA = "8b5e31555919beb083b875b8d38bc2227350ffc950a39308bbd803cefa64d6fa"
BASE = "https://www.haslund.info/10_danmark/30_danmarksturneringen/2025_2026/"
PAGES = {
    "regular_22_rounds": "superliga.asp",
    "championship_10_rounds": "superliga_slut.asp",
    "relegation_10_rounds": "superliga_nedryk.asp",
}
PREVIOUS_WITNESSES = "experiments/263/league_expansion/che_dnk_2526_51_independent_match_score_witnesses_20261114.json"
# Explicitly corroborated because Haslund round list omits FT scores for two
# fixtures. See AGF official match report and independent game statistics.
MISSING_CHAMPIONSHIP_FACTS = [
    {"date":"2026-05-10","home":"Brondby","away":"AGF","ft":[0,2],
     "source_url":"https://www.agf.dk/nyheder/2026/maj/sadan-vandt-vi-dm-i-brondby"},
    {"date":"2026-05-10","home":"Nordsjaelland","away":"Midtjylland","ft":[0,0],
     "source_url":"https://www.worldsoccerdata.com/stats/denmark/superliga/matches/fc-nordsjaelland-vs-fc-midtjylland-10-05-2026"},
]
SOURCE_ALIASES = {
    "FC Nordsjælland":"Nordsjaelland",
    "FC København":"Copenhagen",
    "FC Fredericia":"Fredericia",
    "FC Midtjylland":"Midtjylland",
    "Randers FC":"Randers",
    "Sønderjyske":"Sonderjyske",
    "Brøndby":"Brondby",
    "OB":"Odense",
    "Silkeborg":"Silkeborg"
}
DATE = re.compile(r"(\d{2})\.(\d{2})\.(20(?:25|26))")
FIXTURE = re.compile(r"(?:\d{1,2}:\d{2}\s+)?(.+?)\s+-\s+(.+?)\s+(\d{1,2})\s*-\s*(\d{1,2})(?=\s|$)")
UNSCORED = re.compile(r"(?:\d{1,2}:\d{2}\s+)?(.+?)\s+-\s+(.+?)\s*$")


class TextWithSeparators(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fragments=[]
        self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.skip+=1
        elif tag in ("tr","br","p","div"): self.fragments.append("\n")
        elif tag in ("td","th","span","a"): self.fragments.append(" ")
    def handle_endtag(self,tag):
        if tag in ("script","style") and self.skip: self.skip-=1
        elif tag in ("tr","br","p","div"): self.fragments.append("\n")
        elif tag in ("td","th","span","a"): self.fragments.append(" ")
    def handle_data(self,data):
        if not self.skip: self.fragments.append(data)
    def text(self):
        return "".join(self.fragments).replace("\xa0"," ")


def html_text(raw:bytes)->str:
    for codec in ("utf-8","windows-1252","latin-1"):
        try:
            text=raw.decode(codec)
            break
        except UnicodeDecodeError: continue
    p=TextWithSeparators()
    p.feed(text)
    return p.text()


def club(name:str,look:dict)->str|None:
    clean=name.strip().strip("|").strip()
    return look.get(norm(clean))


def parse_round_list(raw:bytes,section:str)->tuple[dict,dict]:
    t=html_text(raw)
    first=1 if section=="regular_22_rounds" else 23
    start=re.search(r"\b"+str(first)+r"\.\s*RUNDE\b",t)  # exclude preceding lower-case navigation link
    if start is None: raise ValueError("MISSING_START_ROUND_"+section)
    # Do not parse home-v-away score matrix before the detailed date-labelled
    # results; ignore other division links and archived years after the list.
    block=t[start.end():]
    trailing=re.search(r"\bØVRIGE\b",block,re.I)
    if trailing: block=block[:trailing.start()]
    look=name_map("DNK1")
    look.update({norm(k):v for k,v in SOURCE_ALIASES.items()})
    dates=list(DATE.finditer(block))
    found={}
    duplicate=[]
    no_score=[]
    unrecognized=[]
    for i,m in enumerate(dates):
        segment=block[m.end():dates[i+1].start() if i+1<len(dates) else len(block)]
        segment=re.sub(r"\s+"," ",segment).strip()
        # Drop round/attendance-only fragments. Require two known clubs.
        ft=FIXTURE.search(segment)
        if ft:
            home,away=club(ft.group(1),look),club(ft.group(2),look)
            if not home or not away or home==away:
                unrecognized.append({"fragment":segment[:120],"reason":"UNMAPPED_OR_SAME_CLUB"})
                continue
            date_iso=f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            key=(date_iso,home,away)
            score=(int(ft.group(3)),int(ft.group(4)))
            if key in found: duplicate.append(key)
            elif date_iso<"2025-07-01" or date_iso>"2026-06-30": unrecognized.append({"reason":"OUT_OF_DATE","date":date_iso})
            else: found[key]=score
        else:
            looks=UNSCORED.search(segment)
            if looks:
                h,a=club(looks.group(1),look),club(looks.group(2),look)
                if h and a:
                    no_score.append({"date":f"{m.group(3)}-{m.group(2)}-{m.group(1)}","home":h,"away":a})
    return found,{"source_section":section,"date_tokens":len(dates),"parsed":len(found),
                  "duplicate_keys":len(duplicate),"unscored_fixtures":no_score[:10],
                  "unrecognized_line_count":len(unrecognized),
                  "unrecognized_examples":unrecognized[:5]}


def primary_rows(raw:bytes)->dict:
    if hashlib.sha256(raw).hexdigest()!=PRIMARY_SHA:
        raise ValueError("SOURCE_SHA_DRIFT")
    arr=csv_rows(raw.decode("utf-8-sig"))
    if len(arr)!=192: raise ValueError("SOURCE_ROWS_NOT_192")
    look=name_map("DNK1")
    out={}
    for r in arr:
        d=str(r["date"])[:10]
        if str(r.get("status","")).lower() not in ("finished","completed","ft","full-time","full time"):
            raise ValueError("PRIMARY_UNFINISHED")
        h,a=club(r["home"],look),club(r["away"],look)
        if not h or not a or h==a: raise ValueError("PRIMARY_TEAM_UNKNOWN")
        key=(d,h,a)
        if key in out: raise ValueError("PRIMARY_DUPLICATE_MATCH")
        out[key]=(int(r["home_goals"]),int(r["away_goals"]))
    return out


def audit(primary:bytes,sources:dict[str,bytes],old_witnesses:list[dict])->dict:
    main=primary_rows(primary)
    expected_sections={"regular_22_rounds":132,"championship_10_rounds":28,"relegation_10_rounds":30}
    combined={}
    per_section={}
    for name in PAGES:
        parsed,summary=parse_round_list(sources[name],name)
        per_section[name]=summary
        if summary["duplicate_keys"] or summary["unrecognized_line_count"]:
            return {"status":"FAIL_CLOSED_SOURCE_PARSE_ERRORS","per_section":per_section,"trainable_rows":0}
        if len(parsed)!=expected_sections[name]:
            return {"status":"FAIL_CLOSED_SOURCE_SECTION_COUNT","per_section":per_section,
                    "expected_sections":expected_sections,"trainable_rows":0}
        for key,value in parsed.items():
            if key in combined: raise ValueError("REPEATED_FIXTURE_ACROSS_SECTIONS")
            combined[key]=value
    missing_champ_keys={(x["date"],x["home"],x["away"]) for x in MISSING_CHAMPIONSHIP_FACTS}
    if len(missing_champ_keys)!=2: raise ValueError("DUPLICATE_MISSING_CHAMP_KEYS")
    missing_from_primary=set(main)-set(combined)
    if missing_from_primary!=missing_champ_keys:
        return {"status":"FAIL_CLOSED_MISSING_SOURCE_IDENTITIES","per_section":per_section,
                "source_covered":len(combined),"primary_not_in_source_count":len(missing_from_primary),
                "unmatched_examples":[{"date":x[0],"home":x[1],"away":x[2]} for x in sorted(missing_from_primary)[:12]],
                "trainable_rows":0}
    for e in MISSING_CHAMPIONSHIP_FACTS:
        key=(e["date"],e["home"],e["away"])
        if key in combined: raise ValueError("SUPPLEMENT_DUPLICATES_SCORED_LIST")
        combined[key]=tuple(e["ft"])
    matching={k for k in main.keys()&combined.keys() if main[k]==combined[k]}
    differing=sorted((main.keys()&combined.keys())-matching)
    unmatched_primary=sorted(main.keys()-combined.keys())
    unmatched_reference=sorted(combined.keys()-main.keys())
    prev={(w["date"],w["home"],w["away"]) for w in old_witnesses if w["league"]=="DNK1"}
    already_checked=len(prev & matching)
    full=(len(combined)==192 and len(main)==192 and not differing and
          not unmatched_primary and not unmatched_reference and already_checked==15)
    return {
        "status":"FULL_INDEPENDENT_192_MATCH_FT_PASS" if full else "FAIL_CLOSED_MISMATCH",
        "league":"DNK1","season":"2025-26","primary_source_sha256":PRIMARY_SHA,
        "independent_haslund_page_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sources.items()},
        "per_section":per_section,
        "source_total":len(main),"independent_round_list_scored":190,
        "independently_corroborated_missing_championship":2,
        "matched_date_club_ft_score":len(matching),"score_differences":len(differing),
        "source_only_count":len(unmatched_primary),
        "independent_only_count":len(unmatched_reference),
        "previous_15_witnesses_still_matching":already_checked,
        "new_unique_witnesses_beyond_previous_15":len(matching)-already_checked,
        "differences":[{"date":x[0],"home":x[1],"away":x[2],"source_ft":main[x],"independent_ft":combined[x]} for x in differing[:15]],
        "unmatched_source_examples":[{"date":x[0],"home":x[1],"away":x[2]} for x in unmatched_primary[:15]],
        "unmatched_independent_examples":[{"date":x[0],"home":x[1],"away":x[2]} for x in unmatched_reference[:15]],
        "license_to_train_or_rehost":"NOT_ESTABLISHED",
        "raw_upstream_rows_saved":False, "research_quarantine_additions":0,"training_rows_added":0,
        "m4_main_sha_seals_modified":False
    }


def selftest():
    def fake(entries,section):
        start="1. RUNDE" if section=="regular_22_rounds" else "23. RUNDE"
        return ("<html><p>RESULTATER</p><p>"+start+"</p><div>"+
                "".join("<div><a>"+d+"</a> "+line+"</div>" for d,line in entries)+
                "</div><p>ØVRIGE</p></html>").encode("utf-8")
    values=[("20.07.2025","FC Midtjylland - OB 3 - 3 9.813"),
            ("24.08.2025","AGF - Vejle 1 - 0 9.333"),
            ("08.02.2026","Brøndby - Randers FC 0 - 0 16.233")]
    rows,details=parse_round_list(fake(values,"regular_22_rounds"),"regular_22_rounds")
    assert len(rows)==3, details
    assert rows[("2025-07-20","Midtjylland","Odense")]==(3,3)
    assert rows[("2025-08-24","AGF","Vejle")]==(1,0)
    assert rows[("2026-02-08","Brondby","Randers")]==(0,0)
    x,summary=parse_round_list(fake([("10.05.2026","Brøndby - AGF")],"championship_10_rounds"),"championship_10_rounds")
    assert not x and summary["unscored_fixtures"],summary
    print("PASS Danish parser fixture/date/club/score, real 0-0, unscored championship, fail-closed")


def get(url,accept):
    request=Request(url,headers={"User-Agent":"Research-Independent-Football-Source-QA/1.0 (one-time personal analysis)",
                                 "Accept":accept})
    with urlopen(request,timeout=20) as res:
        raw=res.read(2000001)
        if len(raw)>2000000:raise ValueError("SOURCE_SIZE_LIMIT")
    return raw

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--live",action="store_true")
    opts=p.parse_args()
    if opts.self_test:selftest()
    if opts.live:
        payload={"checked_utc":datetime.now(timezone.utc).isoformat(),"scope":"DNK1_2025_26",
                 "status":"NOT_RUN","raw_data_persisted":False,"trainable_rows_added":0}
        try:
            old=json.loads(Path(PREVIOUS_WITNESSES).read_text(encoding="utf-8"))["checks"]
            primary=get(PRIMARY,"text/csv")
            src={name:get(BASE+path,"text/html") for name,path in PAGES.items()}
            payload.update(audit(primary,src,old))
        except Exception as e:
            payload.update({"status":"FAIL_CLOSED_EXCEPTION",
                            "failure_class":type(e).__name__})
        print("DANISH_192_REPORT_START")
        print(json.dumps(payload,ensure_ascii=False,indent=2))
        print("DANISH_192_REPORT_END")
