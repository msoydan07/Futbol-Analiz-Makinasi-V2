#!/usr/bin/env python3
"""Third and FINAL targeted identity fix of exactly 30 new GER2/2026-27
unmatched ODbL-licensed source rows. Do NOT replay 276 verified matches
or any prior 99 existing CC0 old-season rows.
"""
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import check_ger2_odbl_306_new_second_source_once as previous
ROOT=Path("experiments/263/league_expansion/odbl_openligadb_germany2")
PREV=ROOT/"ger2_306_novel_only_second_source_fact_QA_20261114.json"
ODBL=ROOT/"ger2_2026_2027_ODbL_research_quarantine.csv"
SECOND_SHA="dbb98511522cb43ff6d7a08116755b501ad268b6ed346313435b97eee49f3b43"
def inputs():
    r=json.loads(PREV.read_text())
    assert r["status"]=="GER2_NOVEL_306_TARGETED_SECOND_FT_FACT_WITNESS_COMPLETE"
    assert r["by_season"]["2025-26"]["second_FT_exact"]==207
    assert r["by_season"]["2026-27"]["second_FT_exact"]==69
    unresolved=r["by_season"]["2026-27"]["unresolved_original_ODbL_records_only"]["SECOND_SOURCE_MISSING_OR_DATE_TEAM_UNRESOLVED"]
    ids=[int(x["odbl_match_id"]) for x in unresolved]
    assert len(ids)==30 and len(set(ids))==30
    rows=list(csv.DictReader(ODBL.open(encoding="utf-8",newline="")))
    orig={int(row["match_id"]):row for row in rows}
    assert len(rows)==99
    for r in unresolved:
        x=orig[int(r["odbl_match_id"])]
        assert r["date"]==x["date"] and r["home"]==x["home"] and r["away"]==x["away"]
        assert r["odbl_score"]==x["ft_home"]+"-"+x["ft_away"]
    return unresolved
def run():
    original=inputs()
    # New explicit alias names only, no fuzzy team match.
    previous.EXPLICIT.update({
      "wolfsburg":"vfl wolfsburg",
      "cottbus":"energie cottbus",
      "st pauli":"fc st pauli"
    })
    raw=previous.get(previous.URLS["2026-27"])
    if hashlib.sha256(raw).hexdigest()!=SECOND_SHA:
        raise ValueError("SECOND_SOURCE_PIN_CHANGED_NO_30_TARGETED_ADJUDICATION")
    source,flags=previous.independent(raw,"2026-27")
    confirmed=[];notfound=[];disagree=[]
    for row in original:
        key=(row["date"],previous.alias(row["home"]),previous.alias(row["away"]))
        score=source.get(key)
        old=tuple(int(v) for v in row["odbl_score"].split("-"))
        if score is None:notfound.append(row["odbl_match_id"])
        elif score!=old:disagree.append({"odbl_match_id":row["odbl_match_id"],"original_ODbL":row["odbl_score"]})
        else:confirmed.append(row["odbl_match_id"])
    if len(confirmed)+len(notfound)+len(disagree)!=30:raise ValueError("30_TARGET_COUNT_DRIFT")
    return {
      "status":"GER2_2026_27_LAST_30_ALIASES_CHECK_COMPLETE",
      "completed_at_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"Only previous 30 ODbL original score rows with missing 2nd source fixture identity; 276 previously passed source QA strictly frozen",
      "new_aliases":{"Wolfsburg":"VfL Wolfsburg","Cottbus":"Energie Cottbus","St Pauli":"FC St. Pauli"},
      "original_306_novel_rows":306,
      "prior_independent_FT_confirmed_frozen_not_retested":276,
      "this_one_source_only_2026_27_requested":True,
      "targeted_30_independent_exact":len(confirmed),
      "targeted_30_not_found":len(notfound),
      "targeted_30_conflicting_score":len(disagree),
      "targeted_ids_exact":confirmed,
      "remaining_notfound_ODbL_match_ids":notfound,
      "conflicting_original_ODbL_ids_only":disagree,
      "cumulative_novel_306_exact_score_date_home_away":276+len(confirmed),
      "source_sha256_pinned":SECOND_SHA,
      "license_ODbL_original":"https://www.openligadb.de/en/license",
      "other_source_only_in_memory":"https://www.football-data.co.uk/mmz4281/2627/D2.csv",
      "no_external_source_scores_rehosted":True,
      "source_historical_asof_and_license_gates_still_separate":True,
      "new_training_rows_approved":0,
      "old_99_prior_CC0_not_rechecked":True,
      "old_2396_and_296_holds_unchanged":True,
      "M4_and_sealed_predictions_unchanged":True}
def test():
    a=inputs();assert len(a)==30
    assert previous.norm("St. Pauli")=="st pauli"
    assert previous.norm("Energie Cottbus")=="energie cottbus"
    print("PASS exactly 30 old unmatched IDs verified; previously 276 frozen")
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true")
    args=p.parse_args()
    if args.self_test:test()
    if args.live:
        try:report=run()
        except Exception as exc:
            report={"status":"FAIL_CLOSED_EXACT_30_NOT_RECLASSIFIED","error_class":type(exc).__name__,
                 "reason":str(exc)[:200] if isinstance(exc,ValueError) else "HTTP/access/parse error",
                 "new_training_rows_approved":0}
        print("GER2_LAST30_START")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("GER2_LAST30_END")
