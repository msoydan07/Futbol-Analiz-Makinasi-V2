#!/usr/bin/env python3
"""Adjudicate EXACT 96 held ENG5/2025-26 fixtures using one third result witness.
Research-only: no previous 871 checks; no model training; do not rehost third-party rows.
"""
import csv, hashlib, io, json, re, sys
from collections import Counter
from datetime import datetime, date, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_6_leagues_967_scores_one_batch_20261114 as audit
from reconcile_six_leagues_228_exceptions_no_repeat_20261114 import reparse_historical

HERE=Path(__file__).resolve().parent
MANIFEST=HERE/"eng5_2025_26_96_exact_original_FT_conflict_training_HOLD_20261114.csv"
HOLD_BLOB="0a422d9e0a68b6e714852addcb3ec9cf4602a7f6"
KEY_SHA="0fc4455beea8089ce8fca68d575af424f5bc3a3be3efe2a06e41fe8403191f90"
SECOND_SHA="2372229d616a57f9df3d9a401cd942df8e1909ba67017b3793c6aceaf0becf76"
SECOND_URL="https://www.football-data.co.uk/mmz4281/2526/EC.csv"
THIRD_URL="https://www.nonleaguematters.co.uk/divisions/1/16/"
DATE_RE=re.compile(r"^(?:Mon|Tues?|Wednes|Thurs?|Fri|Satur|Sun)day\s+(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s+(20\d{2})$",re.I)

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:
            val=" ".join(data.split())
            if val:self.tokens.append(val)

def original():
    raw=MANIFEST.read_bytes()
    gitsha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if gitsha!=HOLD_BLOB:raise ValueError("EXACT_HOLD_MANIFEST_BLOB_CHANGED")
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    keys=[(r["original_date"],r["home"],r["away"]) for r in rows]
    kh=hashlib.sha256("\n".join("|".join(x) for x in keys).encode()).hexdigest()
    if len(rows)!=96 or len(set(keys))!=96 or kh!=KEY_SHA:
        raise ValueError("EXACT_96_HOLD_KEYS_CHANGED")
    return rows

def fetch(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (historic-research-comparison; one-request-per-source)","Accept":"text/html,text/csv,*/*"})
    with urlopen(req,timeout=28) as response: b=response.read(4_000_001)
    if len(b)>4_000_000:raise ValueError("RESPONSE_SIZE_GUARD")
    return b

def third_parse(raw,clubs):
    if b"National League" not in raw or b"November 2025" not in raw:raise ValueError("NOT_THE_2025_26_NATIONAL_LEAGUE_PAGE")
    h=Visible();h.feed(raw.decode("utf-8",errors="replace"))
    toks=h.tokens
    mapped={};flags=Counter();day=None
    names=audit.exact_name_maps("ENG5",clubs)
    for i,v in enumerate(toks):
        m=DATE_RE.match(v)
        if m:
            try:dd=datetime.strptime(m.group(1)+" "+m.group(2)+" "+m.group(3),"%d %B %Y").date()
            except ValueError:continue
            day=dd if date(2025,8,1)<=dd<=date(2026,6,30) else None
        if v!="NAT" or day is None or i+4>=len(toks):continue
        home,hs,as_,away=toks[i+1:i+5]
        ft=audit.score(hs,as_)
        if ft is None:
            flags["unparsed_score"]+=1;continue
        h=audit.match_name(home,names);a=audit.match_name(away,names)
        if not h or not a or h==a:
            flags["unmapped_team"]+=1;continue
        key=(h,a)
        if key in mapped and mapped[key]!=(day,ft):raise ValueError("THIRD_DUPLICATE_FIXTURE_CONFLICT")
        mapped[key]=(day,ft)
    if len(mapped)<250:raise ValueError("THIRD_SOURCE_INSUFFICIENT_IDENTIFIED_RESULTS:"+str(len(mapped)))
    flags["mapped_third_fixtures_in_memory"]=len(mapped)
    return mapped,dict(flags)

def run():
    original_rows=original()
    clubs={t for r in original_rows for t in (r["home"],r["away"])}
    if len(clubs)!=24:raise ValueError("EXPECTED_24_CLUBS_CHANGED")
    second_raw=fetch(SECOND_URL)  # unchanged SHA guard; query ONLY the 96 HOLD keys
    if hashlib.sha256(second_raw).hexdigest()!=SECOND_SHA:raise ValueError("SECOND_PINNED_SOURCE_DRIFT")
    second,_=reparse_historical(second_raw,"ENG5/2025-26",clubs)
    third_raw=fetch(THIRD_URL)   # independent website; read ONE page, never rehost
    third,diagnostics=third_parse(third_raw,clubs)
    counts=Counter();findings=[]
    for r in original_rows:
        key=(r["home"],r["away"])
        old=(datetime.strptime(r["original_date"],"%Y-%m-%d").date(),
             (int(r["original_home_goals"]),int(r["original_away_goals"])))
        s=second.get(key);t=third.get(key)
        if s is None or t is None:v="MISSING_SECOND_OR_THIRD_PAIR"
        elif s==t and s!=old:v="TWO_EXTERNAL_WITNESSES_AGREE_AGAINST_ORIGINAL"
        elif s[1]==t[1] and s[0]!=t[0]:v="SAME_EXTERNAL_FT_BUT_DATE_NEEDS_REVIEW"
        elif t==old and s!=old:v="THIRD_SUPPORTS_ORIGINAL"
        elif s==t==old:v="NO_LONGER_DISCREPANT"
        else:v="MIXED_THREE_WAY_DISAGREEMENT"
        counts[v]+=1
        findings.append({
          "original_key":"|".join((r["original_date"],r["home"],r["away"])),
          "original_recorded_ft":r["original_home_goals"]+"-"+r["original_away_goals"],
          "verdict":v,
          "external_sources_agree_on_ft":bool(s and t and s[1]==t[1]),
          "external_sources_agree_on_date":bool(s and t and s[0]==t[0]),
          "retain_original_training_hold":True
        })
    assert len(findings)==96 and sum(counts.values())==96
    return {
      "status":"THIRD_SOURCE_TARGETED_96_QA_COMPLETED",
      "checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "original_96_keys_sha256":KEY_SHA,
      "second_pinned_url":SECOND_URL,"second_pinned_sha256":SECOND_SHA,
      "third_witness_url":THIRD_URL,"third_response_sha256":hashlib.sha256(third_raw).hexdigest(),
      "third_source_parse_diagnostics":diagnostics,
      "hold_keys_checked":96,"verdict_totals":dict(counts),
      "per_original_key_flags_only":findings,
      "second_third_raw_scores_exported":False,
      "previous_871_source_matches_retested":0,
      "old_200_ENG3_ENG4_holds_changed":False,
      "original_96_hold_records_modified":False,
      "new_training_matches_approved":0,
      "production_M4_or_old_SHA_changed":False,
      "training_rights_and_historical_feature_vintage_gate":"NOT_CLEARED",
      "third_witness_source_lineage_independence":"NOT_PROVEN",
      "decision":"Continue to hold all 96 original CC0 rows; third-party score facts used only to triage disputes, not replace source rows or promote training."
    }

def self_test():
    assert len(original())==96
    m=Visible()
    m.feed("<b>Tuesday 4th November 2025</b><table><tr><td>NAT</td><td>Boreham Wood</td><td>1</td><td>0</td><td>Aldershot Town</td><td>931</td></tr></table>")
    assert m.tokens==["Tuesday 4th November 2025","NAT","Boreham Wood","1","0","Aldershot Town","931"],m.tokens
    assert DATE_RE.match(m.tokens[0])
    print("PASS frozen 96 keys, no production datasets, date+score HTML parser self test")

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--live",action="store_true")
    args=ap.parse_args()
    if args.self_test:self_test()
    if args.live:
        try:report=run()
        except Exception as e:
            report={"status":"FAIL_CLOSED_NO_ADJUDICATION",
              "error_class":type(e).__name__,
              "reason":str(e)[:350] if isinstance(e,ValueError) else "source access or parsing failed",
              "new_training_matches_approved":0}
        print("ENG5_96_THIRD_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("ENG5_96_THIRD_END")
