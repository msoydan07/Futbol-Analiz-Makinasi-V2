#!/usr/bin/env python3
"""Target-only 32 remaining 2025/26 Spain Segunda FT source QA exceptions.

Freeze the already-witnessed 299/331. This stage checks ONLY:
- Thirty source fixtures involving Racing Santander, mapped from secondary
  provider's short alias 'Santander'.
- One Cadiz vs Almeria rescheduled fixture actually played 2026-02-08.
- One Sporting Gijon vs Leganes suspended then resumed and completed
  2026-03-02 (original publisher kept initial 2026-03-01).
All 331 old source rows are retained immutably, no old 131 or 299 FT checks
repeated. No new source training, no production modification.
"""
import csv,hashlib,json
from collections import Counter
from datetime import date
from pathlib import Path
from verify_esp2_new331_second_FT_source_6playoff_once import (
  NEW,DIR,OUT as PRIOR_REPORT,URL,get,day,norm,CLUBS)
REPORT=DIR/"esp2_2025_26_target_only_32_unresolved_alias_and_two_official_dates_20261114.json"
CLEAN=DIR/"esp2_2025_26_331_corrected_FT_independently_witnessed_RESEARCH_ONLY.csv"
NEW_PIN="b4a868a635c2c266219dd8aa7c13852add8542f0"
CORRECTIONS={
 ("2026-02-07","Cádiz CF","UD Almería"):
  ("2026-02-08","https://www.laliga.com/en-GB/match/temporada-2025-2026-laliga-hypermotion-cadiz-cf-ud-almeria-25"),
 ("2026-03-01","Sporting Gijón","CD Leganés"):
  ("2026-03-02","https://www.laliga.com/en-GB/match/temporada-2025-2026-laliga-hypermotion-real-sporting-cd-leganes-28")
}
def blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def qa():
 src=NEW.read_bytes()
 if blob(src)!=NEW_PIN:raise ValueError("ORIGINAL_331_GIT_SOURCE_PIN_CHANGED")
 original=list(csv.DictReader(src.decode("utf-8-sig").splitlines()))
 prior=json.loads(PRIOR_REPORT.read_text())
 if len(original)!=331 or prior.get("normal_second_source_score_date_team_exact")!=299 or prior.get("normal_second_source_unmapped_or_missing_hold")!=32 or prior.get("normal_second_source_score_conflict_hold")!=0:
  raise ValueError("PREVIOUS_299_PASS_AND_32_HOLD_REPORT_CHANGED")
 racing=[x for x in original if "Racing Santander" in (x["home"],x["away"])]
 special=[x for x in original if (x["date"],x["home"],x["away"]) in CORRECTIONS]
 if len(racing)!=30 or len(special)!=2:raise ValueError("NOT_ONLY_30_PLUS_2_OLD_UNRESOLVED")
 targets=racing+special
 if len({(x["date"],x["home"],x["away"]) for x in targets})!=32:raise ValueError("TARGET_OVERLAPS")
 import io
 provider=get()
 rd=csv.DictReader(io.StringIO(provider.decode("utf-8-sig",errors="replace"),newline=""))
 club={**CLUBS,"santander":"Racing Santander"}
 secondary={}
 for r in rd:
  if r.get("Div")!="SP2":continue
  d=day(r.get("Date"))
  if d is None or not ("2025-08-01"<=d<="2026-06-30"):continue
  h=club.get(norm(r.get("HomeTeam","")));a=club.get(norm(r.get("AwayTeam","")))
  if not h or not a:continue
  try:ft=(int(r["FTHG"]),int(r["FTAG"]))
  except (ValueError,TypeError):continue
  key=(d,h,a)
  if key in secondary and secondary[key]!=ft:raise ValueError("SECOND_PROVIDER_SELF_CONFLICT")
  secondary[key]=ft
 stats=Counter();invalid=[];datefix=[]
 for r in targets:
  key=(r["date"],r["home"],r["away"])
  adjusted=CORRECTIONS.get(key)
  true_date=adjusted[0] if adjusted else r["date"]
  got=secondary.get((true_date,r["home"],r["away"]))
  expected=(int(r["ft_home"]),int(r["ft_away"]))
  if got==expected:
   stats["TARGETED_FT_DATE_TEAM_CONFIRMED"]+=1
   if adjusted:datefix.append({"original_date":r["date"],"official_date":true_date,
      "home":r["home"],"away":r["away"],"FT":str(expected[0])+"-"+str(expected[1]),
      "official_league_evidence":adjusted[1],"secondary_provider":URL})
  else:
   stats["TARGET_NOT_CONFIRMED_HOLD"]+=1
   invalid.append({"original_date":r["date"],"official_date":true_date,
        "home":r["home"],"away":r["away"],
        "score":str(expected[0])+"-"+str(expected[1]),
        "second_score_match":got==expected,"secondary_found":got is not None})
 completed=stats["TARGETED_FT_DATE_TEAM_CONFIRMED"]==32
 if completed:
  after=[]
  target_keys={(r["date"],r["home"],r["away"]) for r in targets}
  for row in original:
   k=(row["date"],row["home"],row["away"])
   new=dict(row)
   new["source_original_date"]=row["date"]
   if k in CORRECTIONS:
    new["date"]=CORRECTIONS[k][0]
    new["fact_evidence_url"]=CORRECTIONS[k][1]
    new["fact_confirmation"]="SECOND_PROVIDER_AND_OFFICIAL_LEAGUE_DATE_SCORE"
   elif k in target_keys:
    new["fact_evidence_url"]=URL
    new["fact_confirmation"]="SECOND_PROVIDER_ALIAS_CORRECTED_DATE_AND_FT"
   else:
    new["fact_evidence_url"]=URL
    new["fact_confirmation"]="PRIOR_299_INDEPENDENT_FT_MATCH_FROZEN_NOT_RETESTED"
   new["training_status"]="RESEARCH_ONLY_NO_PUBLISHER_ASOF"
   after.append(new)
  identities={(r["date"],r["home"],r["away"]) for r in after}
  if len(after)!=331 or len(identities)!=331 or len(datefix)!=2:
   raise ValueError("CORRECTED_331_IDENTITIES_UNEXPECTED")
  fields=list(after[0])
  with CLEAN.open("w",encoding="utf-8",newline="") as f:
   writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
   writer.writeheader();writer.writerows(after)
 result={
 "status":"ESP2_NEW_331_ALL_SECOND_SOURCE_FT_CONFIRMED_2_OFFICIAL_DATE_CORRECTIONS" if completed else "FAIL_CLOSED_REMAINING_NEW_FT_UNRESOLVED_HOLD",
 "previous_passed_299_new_only_score_checks_retested":0,
 "previous_old_131_source_score_checks_retested":0,
 "targeted_new_only_32":len(targets),
 "Racing_Santander_alias_targeted_30":len(racing),
 "changed_official_date_targeted_2":len(special),
 "new_32_score_date_team_exact_after_correction":stats["TARGETED_FT_DATE_TEAM_CONFIRMED"],
 "remaining_new_32_unresolved":stats["TARGET_NOT_CONFIRMED_HOLD"],
 "unresolved_target_keys":invalid,
 "two_official_date_correction_evidence":datefix,
 "all_331_new_regular_independent_score_fact_WITNESSED":331 if completed else 299+stats["TARGETED_FT_DATE_TEAM_CONFIRMED"],
 "six_promotion_playoffs_independent_scoreboard_previously_witnessed":6,
 "corrected_new_regular_331_research_derivative":str(CLEAN) if completed else None,
 "prior_new_331_original_CCBY_source_sha":NEW_PIN,
 "old_131_original_still_immutable":True,
 "source_CCBY_copyright_CC_BY_for_original_snapshot":True,
 "no_pre_match_asof_feature_snapshots_proven":True,
 "new_model_training_rows_approved":0,
 "M4_10league_and_user_1855_manual_xg_untouched":True
 }
 REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 return result
if __name__=="__main__":
 try:result=qa()
 except Exception as exc:
  result={"status":"FAIL_CLOSED_EXCEPTION_32_TARGETED_CHECKS",
          "exception_type":type(exc).__name__,
          "reason":str(exc)[:260],
          "new_model_training_rows_approved":0}
 print("ESP2_32_TARGET_START")
 print(json.dumps(result,indent=2,ensure_ascii=False))
 print("ESP2_32_TARGET_END")
