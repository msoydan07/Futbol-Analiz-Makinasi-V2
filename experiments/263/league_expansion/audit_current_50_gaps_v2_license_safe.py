#!/usr/bin/env python3
"""Research-only CHE1/DNK1 current-season 50 gaps: exact FT score witness audit.

No full score tables are copied into the repository, no right-to-train inferred.
Legacy MatchDaySync CSV changes are compared semantically against immutable
54 CC0 Swiss + 3 Oct 10 facts before any cross-source matching. This script
does not retrain models, edit main, or overwrite SHA prediction seals.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
import csv, hashlib,json,re
from audit_50_2026_27_missing_scores_independent_sources import (
    SOURCES,SWISS_FINAL_ROUND,DANISH_FINAL_FOUR,
    get,names,flatten_records,key_record,parse_stadiro,parse_haslund)
ROOT=Path("experiments/263/league_expansion")
ORIGINAL=ROOT/"cc0_new_485_2526_2627_QUARANTINE_20261113.csv"
NEW3=ROOT/"che1_2026_27_oct10_3_match_score_facts_QUARANTINE_20261114.csv"
VAULT_CHE="https://sportsdatavault.com/en/football/competition/Switzerland/super-league"
VAULT_DNK="https://sportsdatavault.com/en/football/competition/Denmark/superliga"
STADIRO="https://stadiro.com/leagues/switzerland/super-league/results/"
HASLUND="https://www.haslund.info/10_danmark/30_danmarksturneringen/2026_2027/superliga.asp"
ADDITIONAL_NAMES={
 "CHE1":{
   "Zurich":["Zurich","FC Zurich","FC Zürich"],
   "Grasshoppers":["Grasshopper","Grasshopper Club","Grasshopper Club Zürich"],
   "St Gallen":["FC ST. Gallen","St. Gallen","St Gallen"],
 },
 "DNK1":{
   "Brondby":["Broendby IF"],
   "Sonderjyske":["SoenderjyskE","Sønderjyske","SonderjyskE"],
   "Nordsjaelland":["FC Nordsjaelland"],
   "Odense":["OB"],
   "Copenhagen":["FC Copenhagen"],
   "Randers":["Randers FC"],
 },
}
# First party (Swiss FA) and separately published 8 Nov DK result facts.
# Used only for end-of-window missing source records.
OFFICIAL_CHE6=SWISS_FINAL_ROUND
DK_08_NOV4=DANISH_FINAL_FOUR
DK_07_NOV1={("2026-11-07","Odense","Viborg"):(1,2)}

def lookup(league):
    c=names(league)
    for key,alternates in ADDITIONAL_NAMES[league].items():
        for alias in alternates:
            n=c.get(__import__("audit_50_2026_27_missing_scores_independent_sources",fromlist=["norm"]).norm(alias))
            if n not in (None,key):raise ValueError("COLLIDING_ALIAS_"+alias)
            from verify_public_season_csv_2526 import norm
            c[norm(alias)]=key
    return c

class TableCells(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tr=False;self.td=False;self.rows=[];self.cells=[];self.current=[]
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.tr=True;self.cells=[]
        if self.tr and tag in ("td","th"):self.td=True;self.current=[]
    def handle_data(self,data):
        if self.td:self.current.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.td:
            self.cells.append(" ".join("".join(self.current).split()));self.td=False
        if tag=="tr" and self.tr:
            if self.cells:self.rows.append(self.cells)
            self.tr=False

def parse_vault(source,league):
    p=TableCells()
    p.feed(source.decode("utf-8","replace"))
    clubs=lookup(league)
    out={};bad=[];duplicates=0
    for c in p.rows:
        if len(c)<4 or not re.fullmatch(r"2026-(?:10|11)-\d\d",c[0]):continue
        score=re.fullmatch(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})",c[2])
        if not score:continue
        k=key_record(c[0],c[1],c[3],score.group(1),score.group(2),clubs)
        if k:
            key,ft=k
            if key in out:
                duplicates+=1
                if out[key]!=ft:raise ValueError("DATA_VAULT_CONFLICT")
            out[key]=ft
        else:
            bad.append({"date":c[0],"home":c[1],"away":c[3]})
    return out,{"html_table_rows":len(p.rows),"oct_nov_scores":len(out),
                "unmapped_count":len(bad),"unmapped_samples":bad[:5],"duplicate_table_rows":duplicates}

def old_swiss_57():
    c=lookup("CHE1");found={}
    with ORIGINAL.open(encoding="utf-8",newline="") as handle:
        rows=list(csv.DictReader(handle))
    with NEW3.open(encoding="utf-8",newline="") as handle:
        add=list(csv.DictReader(handle))
    for r in rows+add:
        if r["league"]!="CHE1" or r["season"]!="2026-27":continue
        keysc=key_record(r["date"],r["home"],r["away"],r["ft_home"],r["ft_away"],c)
        if keysc is None:raise ValueError("PREVIOUS_57_UNMAPPED")
        key,ft=keysc
        if key in found and found[key]!=ft:raise ValueError("PREVIOUS_57_CONFLICT")
        found[key]=ft
    if len(found)!=57:raise ValueError("EXPECTED_57_NOT_FOUND")
    return found

def audit():
    report={
     "as_of_utc":datetime.now(timezone.utc).isoformat(),
     "source_rights":"THIRD_PARTY_RESULT_TABLE_REHOST_OR_MODEL_TRAINING_NOT_AUTHORIZED",
     "stored_raw_match_tables":False,"new_training_rows":0,"research_quarantine_rows_added":0,
     "production_m4_or_prediction_seals_changed":False,"results":[]}
    for league in ("CHE1","DNK1"):
        r={"league":league,"status":"SOURCE_OR_QA_BLOCKED","stage":"initial"}
        conf=SOURCES[league]
        try:
            r["stage"]="stale_csv_fetch"
            stale_bytes=get(conf["stale"])
            sha=hashlib.sha256(stale_bytes).hexdigest()
            stale,dup=flatten_records(stale_bytes,league)
            if len(stale)!=conf["expected_stale"]:raise ValueError("STALENESS_SOURCE_CARDINALITY_CHANGED")
            r["stale_raw_sha256"]=sha
            r["stale_duplicate_rows"]=dup
            r["stale_normalized_fixtures"]=len(stale)
            r["stale_byte_hash_changed"]=sha!=conf["stale_sha"]
            if league=="CHE1":
                original57=old_swiss_57()
                score_diffs=[k for k in original57 if stale.get(k)!=original57[k]]
                if score_diffs or set(original57)!=set(stale):raise ValueError("STALE_SEMANTIC_DRIFT")
                r["prior_57_score_identity_checks_passed"]=57
            elif sha!=conf["stale_sha"]:
                raise ValueError("DANISH_SOURCE_SHA_CHANGED_WITHOUT_PREVIOUS_SCORE_MANIFEST")
            if league=="CHE1":
                r["stage"]="swiss_data_vault"
                vault_bytes=get(VAULT_CHE)
                vault,diag=parse_vault(vault_bytes,league)
                # Independent Swiss FA final matchday
                fresh={**vault,**OFFICIAL_CHE6}
                r["swiss_vault_diagnostics"]=diag
                r["stage"]="swiss_stadiro_crosscheck"
                other_bytes=get(STADIRO)
                independent,inddiag=parse_stadiro(other_bytes)
                r["swiss_stadiro_diagnostics"]=inddiag
                r["fresh_source_sha256"]=hashlib.sha256(vault_bytes).hexdigest()
                r["second_source_sha256"]=hashlib.sha256(other_bytes).hexdigest()
                expected_direct=24
            else:
                r["stage"]="danish_haslund"
                source_bytes=get(HASLUND)
                from_raw,diag=parse_haslund(source_bytes)
                fresh={**from_raw,**DK_08_NOV4}
                r["danish_haslund_diagnostics"]=diag
                r["stage"]="danish_data_vault_crosscheck"
                other_bytes=get(VAULT_DNK)
                independent,inddiag=parse_vault(other_bytes,league)
                independent.update(DK_08_NOV4)
                independent.update(DK_07_NOV1)
                # Separate Danish 0-0 was omitted as a display placeholder
                # by one public secondary page. Keep only Haslund verified FT.
                r["danish_vault_diagnostics"]=inddiag
                r["fresh_source_sha256"]=hashlib.sha256(source_bytes).hexdigest()
                r["second_source_sha256"]=hashlib.sha256(other_bytes).hexdigest()
                expected_direct=84
            keys_old_missing=set(stale)-set(fresh)
            keys_new=set(fresh)-set(stale)
            conflicts_old=[k for k in set(fresh)&set(stale) if stale[k]!=fresh[k]]
            comparisons=[k for k in keys_new if independent.get(k)==fresh[k]]
            unmatched=[k for k in keys_new if k not in independent]
            mismatches=[k for k in keys_new if k in independent and independent[k]!=fresh[k]]
            gate=(len(fresh)==expected_direct and len(keys_new)==conf["expected_gap"]
                  and len(set(stale)|set(fresh))==conf["expected_all"]
                  and not conflicts_old and not unmatched and not mismatches
                  and len(comparisons)==conf["expected_gap"])
            r.update({
             "source_current_results":len(fresh),"existing_stale_results":len(stale),
             "new_unique_fixtures":len(keys_new),"independent_verified_new_ft_scores":len(comparisons),
             "unknown_new_ft_scores":len(unmatched),"conflicting_new_ft_scores":len(mismatches),
             "old_match_score_conflicts":len(conflicts_old),
             "old_keys_missing_from_new_source":len(keys_old_missing),
             "old_keys_missing_examples":[{"date":k[0],"home":k[1],"away":k[2],"score":list(stale[k])} for k in sorted(keys_old_missing)[:8]],
             "source_covered_unique":len(set(stale)|set(fresh)),
             "expected_covered_unique":conf["expected_all"],
             "new_matches_0_0":sum(fresh[k]==(0,0) for k in keys_new),
             "new_goals_total":sum(sum(fresh[k]) for k in keys_new),
             "unmatched_samples":[{"day":k[0],"home":k[1],"away":k[2]} for k in sorted(unmatched)[:8]],
             "conflict_samples":[{"day":k[0],"home":k[1],"away":k[2]} for k in sorted(mismatches)[:8]],
             "status":"SECOND_SOURCE_ALL_NEW_GAMES_PASS" if gate else "FAIL_CLOSED_UNVERIFIED_OR_MISSING"
            })
        except Exception as exc:
            r.update({"status":"FAIL_CLOSED_SOURCE_OR_QA","error_class":type(exc).__name__,
                      "failure_reason":str(exc)[:100] if isinstance(exc,ValueError) else "provider_blocked",
                      "http_status":getattr(exc,"code",None)})
        report["results"].append(r)
    return report

def selftest():
    assert len(OFFICIAL_CHE6)==6
    assert len(DK_08_NOV4)==4 and len(DK_07_NOV1)==1
    assert len(old_swiss_57())==57
    html_sample=b"<table><tr><th>Date</th><th>Home</th><th>Score</th><th>Away</th></tr><tr><td>2026-10-25</td><td>FC Zurich</td><td>2\xe2\x80\x931</td><td>Luzern</td></tr></table>"
    parsed,diagnostics=parse_vault(html_sample,"CHE1")
    assert parsed[("2026-10-25","Zurich","Luzern")]==(2,1),(parsed,diagnostics)
    print("SELFTEST PASS: exact CC0+3 57 preserved; Swiss/Danish 2026 aliases, HTML table 90-minute score")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--live",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.live:
        print("V2_50_GAP_START")
        print(json.dumps(audit(),indent=2,ensure_ascii=False))
        print("V2_50_GAP_END")
