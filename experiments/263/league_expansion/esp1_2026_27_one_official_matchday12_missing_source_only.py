#!/usr/bin/env python3
"""One NEW official LaLiga MD12 fixture gap check, source date+score only.

Original 4617 research input read-only. LaLiga official 2026/27 week 12
is 10 scored matches Nov6-8, check exactly that cohort using date and score
multiset. Result match identity retained as publicly reported name, not
production UUID unless independently mapped. No old score QA replay.
Do not invent a new match if this round is complete.
"""
from pathlib import Path
from collections import Counter
import csv,hashlib,json
ROOT=Path("experiments/263/league_expansion")
DIR=ROOT/"esp1_2026_27_official_2026_nov8_gap_only"
PROV=Path("data/results_only_263/4617_research_input_provenance.json")
CORE=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
FRESH=ROOT/"2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json"
OFFICIAL="https://www.laliga.com/en-GB/laliga-easports/results/2026-27/gameweek-12"
REF2="https://fbref.com/en/comps/12/schedule/schedule-league-Stats"
DATA=[
 ("2026-11-06","Sevilla FC","Deportivo Alavés",0,0),
 ("2026-11-07","Málaga CF","R. Racing Club",1,2),
 ("2026-11-07","RCD Espanyol de Barcelona","RC Deportivo",0,0),
 ("2026-11-07","CA Osasuna","Athletic Club",1,1),
 ("2026-11-07","Valencia CF","Real Madrid",0,3),
 ("2026-11-08","Elche CF","Real Betis",0,2),
 ("2026-11-08","Real Sociedad","Rayo Vallecano",1,0),
 ("2026-11-08","Celta","Levante UD",0,0),
 ("2026-11-08","Villarreal CF","Getafe CF",2,0),
 ("2026-11-08","Atlético de Madrid","FC Barcelona",1,2)
]
def run():
 prov=json.loads(PROV.read_text());core=CORE.read_bytes()
 if hashlib.sha256(core).hexdigest()!=prov["source_snapshot_sha256"]:raise ValueError("ORIGINAL_4617_CHANGED")
 freshness=json.loads(FRESH.read_text())["counts"]["ESP1"]
 if freshness["persisted_research_or_core"]!=119 or freshness["source_distinct_finished_count"]!=120:
  raise ValueError("OLD_119_NEW_120_SOURCE_COHORT_DRIFT")
 rows=[r for r in csv.DictReader(CORE.open(encoding="utf-8-sig",newline="")) if r["league"]=="ESP1" and r["season"]=="2026-2027"]
 if len(rows)!=119:raise ValueError("NOT_119_ESP1")
 def key(r):return (r["match_date"],int(r["home_goals"]),int(r["away_goals"]))
 source=Counter((d,hg,ag) for d,h,a,hg,ag in DATA)
 existing=Counter(key(r) for r in rows if "2026-11-06"<=r["match_date"]<="2026-11-08")
 excess=existing-source
 # If both scores are same-day identical, a multiset is NOT enough to
 # identify a club: only accept when the date+FT combination occurs once.
 missing=source-existing
 missing_entries=[]
 for (d,h,a,hg,ag) in DATA:
  if missing[(d,hg,ag)]>0 and source[(d,hg,ag)]==1:
   missing_entries.append({"date":d,"home":h,"away":a,"ft_home":hg,"ft_away":ag})
 if excess:status="HOLD_SOURCE_OR_BASELINE_ROUND_NOT_COMPARABLE"
 elif len(missing_entries)==1 and sum(missing.values())==1:status="PASS_EXACT_ONE_OFFICIAL_MD12_NOVEL_FIXTURE_SOURCE_ONLY"
 elif not missing:status="PASS_OFFICIAL_10_ALREADY_PRESENT_ONE_MISSING_IS_EARLIER_ROUND"
 else:status="HOLD_MD12_SOURCE_MISSING_NOT_UNIQUELY_IDENTIFIED"
 DIR.mkdir(parents=True,exist_ok=True)
 if status=="PASS_EXACT_ONE_OFFICIAL_MD12_NOVEL_FIXTURE_SOURCE_ONLY":
  rec=missing_entries[0]
  record={"league":"ESP1","season":"2026-27","date":rec["date"],
          "home":rec["home"],"away":rec["away"],
          "ft_home":rec["ft_home"],"ft_away":rec["ft_away"],
          "stage":"REGULAR_MATCHDAY_12",
          "official_results":OFFICIAL,"independent_witness":REF2,
          "quality_gate":"FACT_SOURCE_RESEARCH_ONLY_NOT_MODEL_TRAINING",
          "source_rights":"ONE_PUBLIC_MATCH_FACT_NOT_RAW_SOURCE_DATABASE_REHOST"}
  p=DIR/"esp1_2026_27_one_official_8nov_missing_source_only.csv"
  with p.open("w",encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=list(record),lineterminator="\n")
   w.writeheader();w.writerow(record)
 out={
 "status":status,
 "source_current_local_ESP1_count":119,
 "source_lagged_new_provider_ESP1_count":120,
 "official_matchday12_total":len(DATA),
 "official_count_same_date_score_in_old":sum(min(existing[k],source[k]) for k in source),
 "official_matchday12_missing_eligible":missing_entries,
 "official_only_matches_added":1 if status=="PASS_EXACT_ONE_OFFICIAL_MD12_NOVEL_FIXTURE_SOURCE_ONLY" else 0,
 "old_4617_main_result_source_modified":False,
 "source_old_ESP1_119_results_score_qa_repeated":False,
 "new_model_training_admissions":0,
 "any_other_2026_27_21_leagues_queried_again":False,
 "name_identity_not_forced_into_existing_uuid_registry":True,
 "source":OFFICIAL,
 "independent":REF2,
 "observation":"date + exact score uniquely identifies a target only when this round has no same-day same-score collision, no claim of licensing bulk API results"
 }
 (DIR/"esp1_2026_27_nov8_source_gap_cannot_guess_20261114.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 return out
if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False,indent=2))
