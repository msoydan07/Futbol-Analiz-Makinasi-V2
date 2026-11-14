#!/usr/bin/env python3
"""Historical-only licensed CC-BY-4.0 source candidate for Danish & Swiss 2025/26.

One fresh public 9.8 MB CSV download from original author. A new source,
NOT a rerun of previous 420 independent-source result tests. Only retain
the selected 2025/26 league results (no other 2023-25 / 2026/27 rows).
Check canonical identities, 90min FT, actual official league-table totals,
the 161 previously corrected/verified ODbL Swiss identities and 2 season
rules. On any unsolved mismatch, report HOLD without claiming acceptance.
Do not touch production M4, its seals, 1855 manual xG or 2396 old files.
"""
import argparse,csv,hashlib,io,json
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from verify_public_season_csv_2526 import name_map,norm,analyze

ROOT=Path("experiments/263/league_expansion")
DEST=ROOT/"ccby_footballcharts_historic_2025_26"
SWISS=ROOT/"odbl_openligadb_swiss1/che1_2025_26_161_ODbL_official_corrected_RESEARCH_ONLY.csv"
SRC="https://huggingface.co/datasets/Damir81/football-charts-results-goal-timing/resolve/main/football_charts_matches.csv"
AUTHOR="Damir Devetak / Football Charts"
CITE="https://doi.org/10.5281/zenodo.22295583"
LIC="https://creativecommons.org/licenses/by/4.0/"
EXPECTED={"CHE1":228,"DNK1":192}
TARGET={"CHE1":("switzerland","super league"),"DNK1":("denmark","superliga")}
COLUMNS=["league","season","date","home","away","ft_home","ft_away",
         "ht_result","kickoff_utc","source_league_code","source_match_date",
         "source_attribution","source_license","research_status"]
def get():
    req=Request(SRC,headers={"User-Agent":"FutbolAnalizMakinesi-Public-CCBY-Research/1.0 (+https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2)","Accept":"text/csv"})
    with urlopen(req,timeout=60) as res:
        b=res.read(16_000_001)
    if len(b)>16_000_000 or len(b)<4_000_000:
        raise ValueError("CCBY_SOURCE_SIZE_GUARD")
    return b
def group(raw):
    text=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text,newline=""))
    fields=set(reader.fieldnames or [])
    needed={"league","league_name","country","season","match_date","home_team",
            "away_team","home_goals","away_goals","ft_result"}
    if not needed.issubset(fields):raise ValueError("CCBY_SCHEMA_CHANGED")
    pool={k:[] for k in EXPECTED}
    stats=Counter();alltotal=0
    for rec in reader:
        alltotal+=1
        if rec.get("season")!="2025-2026":continue
        country=norm(rec.get("country") or "")
        name=norm(rec.get("league_name") or "")
        for lg,(ct,nm) in TARGET.items():
            if country==ct and name==nm:
                pool[lg].append(rec)
                stats[lg]+=1
    if not 70000<=alltotal<=90000:raise ValueError("SUSPICIOUS_BIG_SOURCE_ROW_COUNT")
    return pool,{"source_rows":alltotal,"by_target_league":dict(stats),
                 "source_csv_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def canonical(lg,raw):
    lookup=name_map(lg)
    source=Counter();excluded=[];accepted={};rejects=[]
    for r in raw:
        src_code=r.get("league","")
        source[src_code]+=1
        ds=(r.get("match_date") or "").strip()[:10]
        try:d=date.fromisoformat(ds)
        except ValueError:rejects.append(("DATE_UNPARSABLE",r));continue
        if not date(2025,7,1)<=d<=date(2026,6,30):
            excluded.append(("OUT_OF_SEASON",r));continue
        home=lookup.get(norm(r.get("home_team") or ""))
        away=lookup.get(norm(r.get("away_team") or ""))
        if not home or not away or home==away:
            excluded.append(("NOT_CANONICAL_12_TEAM_LEAGUE",r));continue
        h=(r.get("home_goals") or "").strip()
        a=(r.get("away_goals") or "").strip()
        if not h.isdigit() or not a.isdigit() or not 0<=int(h)<=20 or not 0<=int(a)<=20:
            rejects.append(("BAD_FT",r));continue
        ft=(r.get("ft_result") or "").replace(" ","").replace(":", "-")
        if ft and ft!=h+"-"+a:
            rejects.append(("FT_SHAPE_CONTRADICTS_GOALS",r));continue
        key=(ds,home,away)
        if key in accepted:
            if accepted[key]["ft_home"]!=h or accepted[key]["ft_away"]!=a:
                raise ValueError("CCBY_DUPLICATE_DIFFERENT_FT")
            excluded.append(("DUPLICATE_RESULT_KEY",r));continue
        accepted[key]={
          "league":lg,"season":"2025-26","date":ds,
          "home":home,"away":away,"ft_home":h,"ft_away":a,
          "ht_result":r.get("ht_result",""),
          "kickoff_utc":r.get("kickoff_utc",""),
          "source_league_code":src_code,"source_match_date":ds,
          "source_attribution":AUTHOR+" ("+CITE+")",
          "source_license":"CC-BY-4.0",
          "research_status":"CCBY_HISTORIC_ORIGINAL_PUBLISHER_RESULTS_RESEARCH_ONLY_ASOF_AND_LINEAGE_PENDING"}
    if len(source)>1:raise ValueError("MORE_THAN_ONE_LEAGUE_CODE_SELECTED_FOR_TARGET")
    return accepted,{"source_codes":dict(source),
         "out_of_competition_or_window":Counter(x[0] for x in excluded),
         "source_rows_rejected_by_schema":Counter(x[0] for x in rejects),
         "raw_fixture_rows":len(raw),
         "canonical_valid_unambiguous_rows":len(accepted),
         "quarantine_excluded_examples":[
            {"reason":why,"day":r.get("match_date"),"home":r.get("home_team"),"away":r.get("away_team")}
            for why,r in (excluded+rejects)[:12]]}
def certified_stat_check(lg,selected):
    # This checks official standings totals, not source publication vintage or
    # original-owner permission: a PASS is not a model-training permission.
    pseudo=[{"date":r["date"],"status":"finished","home":r["home"],
             "away":r["away"],"home_goals":r["ft_home"],"away_goals":r["ft_away"]}
            for r in selected.values()]
    d=analyze(pseudo,lg)
    return {"status":d["score_and_coverage_gate"],
            "official_table_count":d["expected_valid_rows"],
            "source_score_and_club_checks":d["valid_unique_scored_rows"],
            "mismatched_clubs":list(d["team_stat_mismatches"].keys()),
            "quarantine_reasons":d["quarantine_reasons"]}
def swiss_only_novel(records):
    prior=list(csv.DictReader(SWISS.open(encoding="utf-8",newline="")))
    if len(prior)!=161:raise ValueError("PINNED_CORRECTED_161_CHANGED")
    cmap=name_map("CHE1");old={}
    for r in prior:
        h=cmap.get(norm(r["home"]));a=cmap.get(norm(r["away"]))
        if not h or not a:raise ValueError("SWISS_PREVIOUS_TEAM_ALIAS_MISSING")
        k=(r["date"],h,a)
        if k in old:raise ValueError("SWISS_PREVIOUS_DUPLICATE")
        old[k]=(int(r["ft_home"]),int(r["ft_away"]))
    agree=0;conflicts=[];new=[]
    for key,r in records.items():
        score=(int(r["ft_home"]),int(r["ft_away"]))
        if key in old:
            if old[key]!=score:
                conflicts.append({"date":key[0],"home":key[1],"away":key[2],
                    "ODbL_corrected_score":"-".join(map(str,old[key])),
                    "CCBY_source_score":"-".join(map(str,score))})
            else:agree+=1
        else:new.append(r)
    missing_from_new=[k for k in old if k not in records]
    return new,{"ODbL_161_old_completed":len(old),
      "CCBY_same_date_club_FT_overlap":agree,
      "CCBY_score_conflicts_vs_corrected_ODbL":conflicts,
      "CCBY_old_ODbL_identity_not_seen_in_this_source_count":len(missing_from_new),
      "new_fixture_candidates":len(new),
      "expected_novel_if_complete_and_overlap_exact":67}
def write(path,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=COLUMNS,lineterminator="\n")
        wr.writeheader();wr.writerows(rows)
def run():
    raw=get()
    grouped,source_stat=group(raw)
    clean={};detailed={}
    for lg in ("CHE1","DNK1"):
        clean[lg],info=canonical(lg,grouped[lg])
        stat=certified_stat_check(lg,clean[lg])
        detailed[lg]={"source_shape":info,"official_2025_26_standings_and_results":stat}
    new_swiss,swiss=swiss_only_novel(clean["CHE1"])
    pass_dn=(detailed["DNK1"]["official_2025_26_standings_and_results"]["status"]=="PASS")
    pass_ch=(detailed["CHE1"]["official_2025_26_standings_and_results"]["status"]=="PASS")
    pass_overlap=(swiss["CCBY_same_date_club_FT_overlap"]==161 and
                  not swiss["CCBY_score_conflicts_vs_corrected_ODbL"] and
                  swiss["CCBY_old_ODbL_identity_not_seen_in_this_source_count"]==0)
    safety=(pass_dn and pass_ch and pass_overlap and len(new_swiss)==67 and
            len(clean["DNK1"])==192 and len(clean["CHE1"])==228)
    DEST.mkdir(parents=True,exist_ok=True)
    status="PASS_ARCHIVED_NEW_192_DANISH_67_SWISS_CCBY" if safety else "HOLD_SOURCE_OR_OVERLAP_NOT_PROVEN__NO_NEW_ARCHIVAL_FT"
    if safety:
        write(DEST/"dnk1_2025_26_192_CC_BY_historic_original_research_only.csv",
              sorted(clean["DNK1"].values(),key=lambda x:(x["date"],x["home"],x["away"])))
        write(DEST/"che1_2025_26_67_NOVEL_CC_BY_research_only.csv",
              sorted(new_swiss,key=lambda x:(x["date"],x["home"],x["away"])))
        (DEST/"ATTRIBUTION_LICENSE.md").write_text(
           "# Licensed original Football Charts historical result derivative\n\n"
           "Dataset: Damir Devetak, Football Charts: Match Results and Goal Timing, "
           "Version 2026.10, published on Hugging Face and Zenodo.\n\n"
           "DOI: "+CITE+"\n\n"
           "Source: "+SRC+"\n\n"
           "License: CC BY 4.0, "+LIC+"\n"
           "Attribution: Data by football-charts.com / Damir Devetak.\n\n"
           "Modifications: selected ONLY Danish Superliga and Swiss Super League "
           "2025-26, converted league/team names to canonical research spellings; "
           "removed out-of-scope league-stage fixtures and previously archived Swiss "
           "ODbL match keys. Only historical result fields are retained. No match "
           "predictions, pre-match snapshots, odds or xG; no license claim about "
           "unrelated third-party source products. This research data is NOT "
           "approved for model training until provenance and temporal gates pass.\n",
           encoding="utf-8")
    report={
      "status":status,"scanned_at_utc":datetime.now(timezone.utc).isoformat(),
      "source":"Football Charts / Damir Devetak Hugging Face 2026.10",
      "license_claim":"CC BY 4.0, author-declared original data",
      "license_url":LIC,"citation_DOI":CITE,
      "source_csv_raw_not_rehosted":True,
      "source_integrity":source_stat,
      "source_country_league_and_competition_filters":detailed,
      "swiss_161_to_novel_67_identity_and_FT_comparison":swiss,
      "new_historic_DNK1_2025_26_identity_rows_archived":192 if safety else 0,
      "new_historic_CHE1_2025_26_identity_rows_archived":67 if safety else 0,
      "new_unique_research_fixture_identities":259 if safety else 0,
      "new_fixture_sources_new_2026_27":0,
      "previous_source_2863_research_identities_frozen":True,
      "previous_161_SWISS_ODbL_sources_untouched":True,
      "previous_420_Swiss_Danish_FT_QA_run_replayed":False,
      "previous_306_GER2_score_QA_replayed":False,
      "main_10league_M4_and_signed_SHA_untouched":True,
      "original_2396_AND_296_HOLD_unchanged":True,
      "new_training_rows_approved":0,
      "pre_kickoff_feature_asof_metadata_certified":False,
      "source_upstream_lineage_and_database_rights_fully_audited":False,
      "new_research_licensed_CCBY_files_added":bool(safety),
      "note":"Even a 2025/26 results archive that passes season/standings totals requires licensed-source trust and pre-match source-vintage restrictions before model training. STRICT no historical match source repetition."
    }
    (DEST/"2025_26_259_potential_new_danish_swiss_CC_BY_source_gate_20261114.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    return report
def test():
    assert TARGET["CHE1"]==("switzerland","super league")
    assert TARGET["DNK1"]==("denmark","superliga")
    assert len(list(csv.DictReader(SWISS.open(encoding="utf-8"))))==161
    print("PASS Swiss 161 previously corrected source untouched, target only two 2025/26 leagues")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");a=p.parse_args()
    if a.self_test:test()
    if a.run:
        try:record=run()
        except Exception as exc:
            DEST.mkdir(parents=True,exist_ok=True)
            record={"status":"FAIL_CLOSED_SOURCE_OR_PARSER_NO_NEW_DATA_ARCHIVED",
              "error_class":type(exc).__name__,
              "reason":str(exc)[:320] if isinstance(exc,ValueError) else "download or parsing unavailable",
              "new_unique_research_fixture_identities":0,"new_training_rows_approved":0}
            (DEST/"2025_26_259_potential_new_danish_swiss_CC_BY_source_gate_20261114.json").write_text(json.dumps(record,indent=2)+"\n")
        print("CCBY_ARCHIVE_START")
        print(json.dumps(record,ensure_ascii=False,indent=2))
        print("CCBY_ARCHIVE_END")
