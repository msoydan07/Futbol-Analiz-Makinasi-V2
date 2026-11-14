#!/usr/bin/env python3
"""Belgian 2025/26 311-score source vs ACTUAL playoff structure.

Existing core 4617 SHA is frozen. This is a new *stage coverage* QA dimension,
not repeating previous 4617 per-result FT validations or altering M4.
Uses 2025/26 Pro League official 240 regular (30 rounds), champion top6
30, Europe top6 30, relegation bottom4 12, plus Gent-Genk special final
May31 and promotion/relegation ties May17 &23 (other competitions).
Match metadata/UUID and match score are not republished in report.
"""
from pathlib import Path
import csv,hashlib,json
from collections import Counter,defaultdict
ROOT=Path("experiments/263/league_expansion")
IN=Path("data/results_only_263/2026-11-10_completed_4617_scores_only.csv")
PROV=Path("data/results_only_263/4617_research_input_provenance.json")
OUT=ROOT/"bel1_2025_26_311_core_stage_graph_missing_fixtures_20261114.json"
def run():
 p=json.loads(PROV.read_text())
 raw=IN.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=p["source_snapshot_sha256"]:
  raise ValueError("CORE_4617_CHANGED_FAIL_CLOSED")
 allrows=list(csv.DictReader(IN.open(encoding="utf-8-sig",newline="")))
 rows=[r for r in allrows if r["league"]=="BEL1" and r["season"]=="2025-2026"]
 if len(rows)!=311:raise ValueError("BEL_311_SOURCE_ROW_DRIFT")
 regs=[r for r in rows if r["match_date"]<="2026-03-22"]
 groups=[r for r in rows if "2026-04-01"<=r["match_date"]<="2026-05-26"]
 specials=[r for r in rows if r["match_date"]>"2026-05-26"]
 months=Counter(r["match_date"][:7] for r in rows)
 dates=Counter(r["match_date"] for r in rows)
 team={x for r in rows for x in (r["home_id"],r["away_id"])}
 # Detect group networks using core ID's; no guessed name alias, no importing
 # external source score tables. A playoff group is a connected component.
 graph=defaultdict(set)
 for r in groups:
  h=r["home_id"];a=r["away_id"]
  graph[h].add(a);graph[a].add(h)
 components=[];seen=set()
 for key in graph:
  if key in seen:continue
  pending=[key];seen.add(key);members=set()
  while pending:
   cur=pending.pop();members.add(cur)
   for z in graph[cur]:
    if z not in seen:seen.add(z);pending.append(z)
  components.append(members)
 components.sort(key=lambda g:(-len(g),sorted(g)[0]))
 comp_out=[]
 for c in components:
  inside=[r for r in groups if r["home_id"] in c and r["away_id"] in c]
  directed=Counter((r["home_id"],r["away_id"]) for r in inside)
  expected=len(c)*(len(c)-1)
  missing=[(a,b) for a in c for b in c if a!=b and directed[(a,b)]==0]
  duplicate=sum(v-1 for v in directed.values() if v>1)
  comp_out.append({
   "group_size":len(c),"count_actual":len(inside),
   "expected_complete_double_round_robin":expected,
   "missing_directed_fixture_count":len(missing),
   "duplicate_directed_fixture_count":duplicate,
   "missing_internal_team_uuid_hashes_not_real_names":[
      {"home_uuid_prefix":a[:12],"away_uuid_prefix":b[:12]} for a,b in sorted(missing)[:12]]
  })
 status="PASS_NAMED_COMPETITION_FORMAT_STAGE_GAPS_LOCALIZED__OR_HOLD" if len(regs)==240 else "HOLD_REGULAR_240_NOT_COMPLETE"
 out={
  "status":status,
  "old_core_source_4617_SHA_untouched":True,
  "old_BEL1_2025_26_scored_source_rows":311,
  "normal_stage_until_2026_03_22":len(regs),
  "separately_grouped_2026_04_01_thru_2026_05_26":len(groups),
  "after_group_or_cross_tier_in_core_after_2026_05_26":len(specials),
  "source_month_counts":dict(sorted(months.items())),
  "observed_playoff_component_sizes":[x["group_size"] for x in comp_out],
  "components":comp_out,
  "official_format_ref":"https://www.proleague.be/nieuws/grote-lijnen-van-seizoen-2025-2026-ligt-vast",
  "season_results_ref":"https://www.rsssf.org/tablesb/belg2026.html",
  "expected_playoff_group_games":72,
  "expected_regular_games":240,
  "special_european_final_Gent_Genk_2026_05_31_ref":"https://fbref.com/en/comps/37/2025-2026/schedule/2025-2026-Belgian-Pro-League-Scores-and-Fixtures",
  "new_persisted_match_ids":0,
  "no_source_score_revalidation":True,
  "new_model_training_approved":0,
  "note":"Only a stage/fixture-count graph, not a second score validation. Missing actual fixture gets HOLD, no fabricated match score; an extra Gent–Genk final not in standard group competition must be separately stage-tagged."
 }
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 return out
if __name__=="__main__":
 print(json.dumps(run(),ensure_ascii=False,indent=2))
