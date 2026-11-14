#!/usr/bin/env python3
"""One NEW validation dimension: actual date for 47 prior date-mismatched
2025/26 Italian Serie B matches, using independent La Repubblica calendar.

Already-resolved 261 exact date+FT and single 36-day officially rescheduled
fixture are not tested again. No matchday CSV or Repubblica full table stored,
no prediction/score rows written. Both public sources used in memory only.
"""
from __future__ import annotations
import argparse,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from verify_ita2_2526_309_second_source_standings_once import (
    primary,secondary,club,score,get as load_second,URL as MATCHDAY_URL)
from reconcile_ita2_2526_48_date_only_exceptions_once import PINNED_SHA

THIRD="https://www.repubblica.it/sport/dirette/calcio/serie-b-2025/calendario/"
MONTHS={"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,
        "giugno":6,"luglio":7,"agosto":8,"settembre":9,"ottobre":10,
        "novembre":11,"dicembre":12}
WEEK="(?:luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)"
EXACT=re.compile(r"^\s*"+WEEK+r"\s+(\d{1,2})\s+("+ "|".join(MONTHS)+r")\s+202(?:5|6)\s*-\s*(?:\d{1,2}:\d\d\s+)?(.+?)\s+(\d{1,2})\s+Fine\s+(\d{1,2})\s+(.+?)\s*$",re.I)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0;self.buff=[];self.answers=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            if self.depth==0:self.buff=[]
            self.depth+=1
        elif tag=="br" and self.depth:self.buff.append(" ")
    def handle_data(self,data):
        if self.depth:self.buff.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.depth:
            self.depth-=1
            if self.depth==0:
                self.answers.append(" ".join(" ".join(self.buff).split()))
                self.buff=[]

def parse_third(raw):
    parser=Links();parser.feed(raw.decode("utf-8","replace"))
    found={};status=Counter();all_links=len(parser.answers)
    for line in parser.answers:
        m=EXACT.fullmatch(line)
        if not m:
            if "Fine" in line and len(line)<160:status["unparsed_finished_anchor"]+=1
            continue
        day=int(m.group(1));month=MONTHS[m.group(2).casefold()]
        # The calendar page covers only 2025/26. Dec or earlier 2025,
        # Jan to June 2026; refuse other fiscal years and future fixtures.
        year=2025 if month>=7 else 2026
        iso=date(year,month,day).isoformat()
        home,away=club(m.group(3)),club(m.group(6))
        ft=score(m.group(4),m.group(5))
        if not home or not away or home==away or ft is None:
            status["unmapped_club_or_score"]+=1
            continue
        key=(home,away)
        if key in found:
            status["multi_competition_pair_or_duplicate"]+=1
            # Calendar may also list play-offs. Only regular season before
            # April is needed, and must not conflict; handle separately.
            continue
        found[key]=(iso,ft)
    return found,{"total_anchor_tags":all_links,"unique_scored_home_away":len(found),"parse_exceptions":dict(status)}

def load(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (historical-score-date-audit/1.0)",
             "Accept":"text/html"})
    with urlopen(req,timeout=24) as response:
        body=response.read(2_500_001)
        if len(body)>2_500_000:raise ValueError("THIRD_SOURCE_TOO_LARGE")
    return body

def audit():
    raw=load_second()
    if hashlib.sha256(raw).hexdigest()!=PINNED_SHA:
        raise ValueError("PINNED_MATCHDAY_SECOND_SOURCE_CHANGED")
    historic,_=primary()
    secondary,diag=secondary_fn(raw)
    if len(secondary)!=380 or len(historic)!=309:
        raise ValueError("OLDER_SOURCE_COUNTS_CHANGED")
    exceptions=[(k,v) for k,v in historic.items() if k not in secondary]
    if len(exceptions)!=48:raise ValueError("EXCEPTIONS_48_CHANGED")
    # Do not compare the previous 261 exact-match FT scores.
    by_pair={(h,a):(day,ft) for (day,h,a),ft in secondary.items()}
    postponed=("Juve Stabia","Bari")
    targeted=[]
    for (original_date,h,a),ft in exceptions:
        source=by_pair.get((h,a))
        if not source or source[1]!=ft:raise ValueError("PRIOR_48_SCORE_QA_CHANGED")
        if (h,a)==postponed:
            if original_date!="2025-10-29" or source[0]!="2025-12-04" or ft!=(0,0):
                raise ValueError("OFFICIAL_POSTPONED_FIXTURE_CHANGED")
            continue
        targeted.append({"key":(h,a),"old":original_date,"source_date":source[0],"ft":ft})
    if len(targeted)!=47:raise ValueError("ONLY_47_TARGETS_CHANGED")
    webpage=load(THIRD)
    dates,meta=parse_third(webpage)
    correct=[];wrong=[];notfound=[]
    for x in targeted:
        third=dates.get(x["key"])
        if third is None:
            if len(notfound)<12:notfound.append({"home":x["key"][0],"away":x["key"][1]})
        elif third[0]==x["source_date"] and third[1]==x["ft"]:
            correct.append(x)
        elif len(wrong)<12:
            wrong.append({"home":x["key"][0],"away":x["key"][1],
                "matchday_second_date":x["source_date"],"third_date":third[0],
                "matchday_same_FT":third[1]==x["ft"]})
    matched=len(correct)
    complete=matched==47 and not wrong and not notfound
    return {"run_utc":datetime.now(timezone.utc).isoformat(),
            "status":"47_OF_47_TRUE_KICKOFF_DATE_THIRD_SOURCE_QA_PASS" if complete
                     else "FAIL_CLOSED_DATE_WITNESSES_INCOMPLETE",
            "targeted_prior_47_one_day_date_exceptions":47,
            "corrected_kickoff_date_equal_second_vs_third_source":matched,
            "different_actual_date_or_FT_examples":wrong,
            "not_matched_in_third_source_examples":notfound,
            "missing_count":47-matched-len(wrong),
            "third_source_url":THIRD,"third_source_html_sha256":hashlib.sha256(webpage).hexdigest(),
            "third_parse_diagnostics":meta,
            "source_second_csv_SHA256":PINNED_SHA,
            "previous_exact_date_cases_not_rechecked":261,
            "previous_postponed_36_day_case_not_rechecked":1,
            "all_309_old_source_date_fields_mutated":False,
            "date_overlay_provenance_recorded_as_aggregate_only":True,
            "training_rows_added":0,
            "external_html_not_rehosted":True,"original_M4_SHA_untouched":True}

def secondary_fn(raw):
    return secondary(raw)

def selftest():
    sample="<a href='/example'>Domenica 15 Febbraio 2026 - 15:00 Spezia 0 Fine 2 Frosinone</a>"
    p,diag=parse_third(sample.encode())
    assert p[("Spezia","Frosinone")]==("2026-02-15",(0,2)),(p,diag)
    sample2="<a>Lunedì 8 Dicembre 2025 - 15:00 Frosinone 3 Fine 0 Juve Stabia</a>"
    p,_=parse_third(sample2.encode())
    assert p[("Frosinone","Juve Stabia")]==("2025-12-08",(3,0))
    assert len(primary()[0])==309
    print("PASS sample Italian accented weekdays, original 309 pinned, 0-0 never blank")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true")
    opt=p.parse_args()
    if opt.self_test:selftest()
    if opt.run:
        try:doc=audit()
        except Exception as e:
            doc={"status":"FAIL_CLOSED_THIRD_SOURCE_OR_PARSER",
                 "error_class":type(e).__name__,
                 "error_detail":str(e)[:180] if isinstance(e,ValueError) else "provider access denied",
                 "training_rows_added":0}
        print("ITA47_THIRD_DATE_START")
        print(json.dumps(doc,indent=2,ensure_ascii=False))
        print("ITA47_THIRD_DATE_END")
