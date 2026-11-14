#!/usr/bin/env python3
"""One *new league scope* extraction: 2025/26 Spain Segunda from pinned original
Football Charts CC-BY historical snapshot. First time archiving this source
league, not replaying previous QA. Archive source-author subset with attribution,
keep 131 old OpenFootball match identities unchanged, no training/prediction.
Source read once, pinned SHA256; output source-specific archive and diagnostics.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion")
OUT=ROOT/"ccby_footballcharts_esp2_2025_26_original_source"
SRC="https://huggingface.co/datasets/Damir81/football-charts-results-goal-timing/resolve/main/football_charts_matches.csv"
PIN="08d1a0863d703550fe6e7fb1ef9faed4ea3cea95c664012373b1a1e1f159be10"
SRC_LABEL="spain2"
DOI="https://doi.org/10.5281/zenodo.22295583"
FIELDS=["league","season","date","source_home","source_away","source_ft_home","source_ft_away",
        "source_ht_result","source_kickoff_utc","source_league_code",
        "source_competition_name","source_license","source_doi","gate","stage_gate","asof_gate"]
def download():
 req=Request(SRC,headers={"Accept":"text/csv","User-Agent":"FutbolAnaliz263-2025-26-ESP2-FirstOriginalScope/0.1"})
 with urlopen(req,timeout=45) as f:
  data=f.read(17_000_001)
 if len(data)>17_000_000 or hashlib.sha256(data).hexdigest()!=PIN:
  raise ValueError("ORIGINAL_PUBLISHER_SNAPSHOT_CHANGED_FAIL_CLOSED")
 return data
def main():
 data=download()
 original=csv.DictReader(io.StringIO(data.decode("utf-8-sig"),newline=""))
 req={"country","league_name","league","season","match_date","home_team","away_team","home_goals","away_goals","ft_result"}
 if not req.issubset(original.fieldnames or []):raise ValueError("ORIGINAL_DATA_SCHEMA_CHANGED")
 allrows=[];sourceN=0
 for r in original:
  if r.get("country")!="Spain" or r.get("season")!="2025-2026" or r.get("league")!=SRC_LABEL:
   continue
  sourceN+=1
  ds=(r.get("match_date") or "")[:10]
  try:date.fromisoformat(ds)
  except ValueError:raise ValueError("SOURCE_DATE_UNPARSEABLE")
  home=(r.get("home_team") or "").strip();away=(r.get("away_team") or "").strip()
  hg=str(r.get("home_goals") or "").strip();ag=str(r.get("away_goals") or "").strip()
  if not home or not away or home==away or not hg.isdigit() or not ag.isdigit() or max(int(hg),int(ag))>30:
   raise ValueError("SOURCE_INVALID_FT_TEAM")
  ft=(r.get("ft_result") or "").strip().replace(":","-").replace(" ","")
  if ft and ft!=hg+"-"+ag:raise ValueError("SOURCE_FT_SCORE_MISMATCH")
  allrows.append({
    "league":"ESP2","season":"2025-26","date":ds,"source_home":home,"source_away":away,
    "source_ft_home":hg,"source_ft_away":ag,
    "source_ht_result":r.get("ht_result") or "",
    "source_kickoff_utc":r.get("kickoff_utc") or "",
    "source_league_code":SRC_LABEL,
    "source_competition_name":r.get("league_name") or "",
    "source_license":"CC-BY-4.0",
    "source_doi":DOI,"gate":"CCBY_ORIGINAL_PUBLISHER_RESEARCH_SOURCE_QUARANTINE",
    "stage_gate":"FULL_SEASON_FT_REGULAR_STAGE_NOT_YET_CERTIFIED",
    "asof_gate":"NO_PREMATCH_OBSERVED_AT_FEATURE_PROOF"})
 if len(allrows)!=509:raise ValueError("SPAIN2_ORIGINAL_LABEL_ROW_COUNT_CHANGED:"+str(len(allrows)))
 bydate=Counter();club=Counter();ident=Counter();days=defaultdict(list)
 for r in allrows:
  key=(r["date"],r["source_home"],r["source_away"])
  ident[key]+=1
  bydate[r["date"][:7]]+=1
  club[r["source_home"]]+=1;club[r["source_away"]]+=1
  days[r["date"]].append(r)
 pre=[r for r in allrows if r["date"]<="2026-05-31"]
 post=[r for r in allrows if r["date"]>"2026-05-31"]
 directed=Counter((r["source_home"],r["source_away"]) for r in pre)
 regular_clubs={x for r in pre for x in (r["source_home"],r["source_away"])}
 stage={
  "source_509_scorable_rows":len(allrows),"through_2026_05_31":len(pre),
  "after_2026_05_31":len(post),
  "distinct_clubs_in_pre_cutoff":len(regular_clubs),
  "club_appearance_min_max_pre_cutoff":([min(club.values()),max(club.values())] if club else None),
  "all_source_exact_date_team_duplicates":sum(n-1 for n in ident.values()),
  "pre_cutoff_duplicate_directed_fixture_pairs":sum(n-1 for n in directed.values()),
  "pre_cutoff_462_regular_round_robin_verified":
   len(pre)==462 and len(regular_clubs)==22 and len(directed)==462 and all(v==1 for v in directed.values())
   and all(sum(1 for r in pre if r["source_home"]==c or r["source_away"]==c)==42 for c in regular_clubs),
  "post_cutoff_date_counts":dict(sorted(Counter(r["date"] for r in post).items())),
  "source_monthly_counts":dict(sorted(bydate.items())),
  "source_competition_distinct_names":dict(Counter(r["source_competition_name"] for r in allrows)),
  "source_team_names":sorted(regular_clubs),
  "note":"509 original source rows are NOT 509 distinct regular games, and aren't auto-added to 4505 until stage, identity and second-source QA."
 }
 OUT.mkdir(parents=True,exist_ok=True)
 allrows.sort(key=lambda r:(r["date"],r["source_home"],r["source_away"]))
 out=OUT/"esp2_2025_26_509_CC_BY_original_source_QUIET_RESEARCH.csv"
 with out.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
  w.writeheader();w.writerows(allrows)
 report={
  "status":"PASS_ORIGINAL_ESP2_2025_26_CCBY_LICENSE_SOURCE_509_RESEARCH_ROWS_ARCHIVED_NOT_DEDUP_OR_TRAINING",
  "snapshot_sha256":PIN,"license":"CC BY 4.0","attribution":"Football Charts / Damir Devetak",
  "source_doi":DOI,"source_url":SRC,
  "new_source_specific_esp2_rows":len(allrows),
  "source_filename":str(out),
  "full_source_not_rehosted":True,
  "source_form_tests":stage,
  "old_131_ESp2_existing_research_IDs_not_changed":True,
  "old_4505_research_unique_identities_not_incremented":True,
  "new_model_training_approved":0,
  "next_distinct":"Reconcile new source 509 with old 131; identify 462 true regular season using exact team/date schedule; separately handle six promotion playoffs and any source duplicates/nonmatches. Only then count new novel identities."
 }
 (OUT/"esp2_2025_26_original_509_source_scope_QA_20261114.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 (OUT/"ATTRIBUTION_LICENSE.md").write_text(
 "# ESP2 2025/26 original publisher research source\n\nData by Football Charts (Damir Devetak), source snapshot CC BY 4.0.\n"
 "DOI: "+DOI+"\nLicense: https://creativecommons.org/licenses/by/4.0/\n"
 "Filtered source author's 2025-26 Spain La Liga2 archive, score-format validated; no original full 76,991 source dataset rehosted.\n"
 "No dedup, stage proof, independent score QA or historical as-of / training permission verified. No M4 changes.\n",encoding="utf-8")
 return report
def test():
 assert SRC_LABEL=="spain2"
 assert date.fromisoformat("2026-05-31")<date(2026,11,13)
 print("PASS source limited to Spain La Liga2 2025/26 under pinned CC BY historical publisher source")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");a=p.parse_args()
 if a.self_test:test()
 if a.run:
  try:d=main()
  except Exception as exc:
   d={"status":"FAIL_CLOSED_NEW_ESP2_SOURCE_NOT_ACCEPTED",
      "error_class":type(exc).__name__,"error":str(exc)[:250],
      "new_model_training_approved":0}
  print("ESP2_SOURCE_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("ESP2_SOURCE_END")
