"""Offline evidence audit for 28 new official/club score observations.

NEVER downloads Football-Data or official league pages. Tests what has
been recorded and source classes, NOT whether a website was visited by CI.
No adoption into original 4518 history, no score attestation or M4 changes.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

LEAGUES={"ESP1":("www.laliga.com","OFFICIAL_LEAGUE_MATCHDAY_PAGE",10),
         "NED1":("www.knvb.nl","OFFICIAL_FEDERATION_RESULTS_PAGE_PROVISIONAL",9),
         "FRA1":("www.psg.fr","OFFICIAL_CLUB_WEEKLY_COMPILATION_NOT_LEAGUE_ATTESTATION",9)}
ALLOWED_COUNTS={"TUR1":9,"GER1":9,"ITA1":10}
DATA_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
class EvidenceError(ValueError):pass

def require(statement,label):
    if not statement:raise EvidenceError(label)

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def check_new(doc, registry, old):
    require(doc.get("schema")=="263_ADDITIONAL_28_PUBLISHED_SCORE_OBSERVATIONS_V1","WRONG_NEW_LEDGER_SCHEMA")
    require(doc.get("observation_cutoff")=="2026-11-10","WRONG_SNAPSHOT_DAY")
    obs=doc.get("records")
    require(type(obs)==list and len(obs)==28,"NEW_PUBLIC_SCORE_COUNT_NOT_28")
    require(doc.get("no_supplier_download_due_to_already_used_twice_this_week") is True,"SOURCE_BUDGET_UNSAFE")
    require(doc.get("original_28_research_csv_concordant_unchanged") is True,"PREVIOUS_SOURCE_INVALID")
    known=set()
    for row in old["records"]:
        known.add((row["league"],row["date"],row["home_id"],row["away_id"]))
    memberships=registry["season_memberships"]["2026-2027"]
    aliases=registry["aliases"];by=Counter()
    for x in obs:
        require(set(x)=={"league","match_date","home_alias","away_alias","home_id",
          "away_id","home_goals","away_goals","result","score_evidence_url",
          "score_evidence_type","score_evidence_note","official_fixture_id",
          "source_supplier_crosscheck","observation_status"}, "RECORD_SCHEMA_MISMATCH")
        league=x["league"]
        require(league in LEAGUES,"UNKNOWN_ADDITIONAL_LEAGUE")
        host,label,expected=LEAGUES[league]
        u=urlsplit(x["score_evidence_url"])
        require(u.scheme=="https" and u.hostname==host and len(u.path)>3,"UNAPPROVED_SOURCE_WEBPAGE")
        require(x["score_evidence_type"]==label,"UNEXPECTED_EVIDENCE_TYPE")
        require(x["source_supplier_crosscheck"]=="NOT_CHECKED_SOURCE_WEEKLY_ACCESS_LIMIT","FALSE_PROVIDER_CONCORDANCE")
        require(x["observation_status"]=="EXTERNAL_PAGE_READ_AS_RESEARCH_NOT_API_VERIFIED","FALSE_INDEPENDENT_ATTESTATION")
        require(x["official_fixture_id"] is None,"INVENTED_OFFICIAL_FIXTURE_ID")
        require(type(x["home_goals"]) is int and type(x["away_goals"]) is int and
           0<=x["home_goals"]<=20 and 0<=x["away_goals"]<=20,"INVALID_SCORE")
        require(x["result"]==("H" if x["home_goals"]>x["away_goals"] else
                     "D" if x["home_goals"]==x["away_goals"] else "A"),"RESULT_SCORE_CONTRADICTION")
        require(date(2026,11,6)<=date.fromisoformat(x["match_date"])<=date(2026,11,8),"OUT_OF_SCOPE_DATE")
        for side in ("home","away"):
            require(aliases.get(x[side+"_alias"])==x[side+"_id"],"TEAM_ALIAS_CANONICAL_ID_DIFFER")
            require(x[side+"_id"] in memberships[league],"TEAM_NOT_IN_2026_27_COMPETITION")
        require(x["home_id"]!=x["away_id"],"SAME_TEAM_BOTH_SIDES")
        key=(league,x["match_date"],x["home_id"],x["away_id"])
        require(key not in known,"REPEATED_CANONICAL_FIXTURE")
        known.add(key)
        by[league]+=1
    require(by==Counter({k:v[2] for k,v in LEAGUES.items()}),"DIFFERENT_MATCHDAY_COUNTS")
    return dict(by)

def audit(root):
    root=Path(root)
    old=load(root/"research/opponent_goals/official_rounds_nov06_08_2026.json")
    new=load(root/"research/opponent_goals/official_additional_28_nov06_08_2026.json")
    registry=load(root/"experiments/263/evidence/identity_index_263.json")
    prior=load(root/"research/opponent_goals/reports/official_round_score_concordance_20261110.json")
    inv=load(root/"research/opponent_goals/reports/current_source_preflight_20261110.json")
    hist=root/"data/quad_accepted_263/extended_history.csv"
    require(hashlib.sha256(hist.read_bytes()).hexdigest()==DATA_SHA,"ORIGINAL_HISTORY_BYTES_TAMPERED")
    require(len(old["records"])==28,"ORIGINAL_OFFICIAL_28_CHANGED")
    require(Counter(x["league"] for x in old["records"])==Counter(ALLOWED_COUNTS),"OLD_OFFICIAL_COUNTS_WRONG")
    require(prior["status"]=="RESEARCH_MATCHED_OFFICIAL_ROUNDS_NOT_OFFICIAL_MATCH_ID_ATTESTED" and
           prior["official_provider_concordant_count"]==28 and
           prior["provider_new_candidates_total"]==99 and
           prior["provisional_not_officially_checked_count"]==71,
           "PREVIOUS_SOURCE_CROSSCHECK_EVIDENCE_WRONG")
    require(inv.get("source_4518_sha256")==DATA_SHA,"NEW_99_SOURCE_RECEIPT_INVALID")
    groups=check_new(new,registry,old)
    count_old=prior["official_provider_concordant_count"]
    count_new=sum(groups.values())
    observed=count_old+count_new
    total=prior["provider_new_candidates_total"]
    require(observed<=total and total==99,"DOUBLE_COUNT_OR_MISSING_FROZEN_COHORT")
    return {
      "schema":"263_ADDITIONAL_28_SCORE_OBSERVATION_OFFLINE_AUDIT_V1",
      "status":"ADDITIONAL_OFFICIAL_OR_CLUB_SIDE_SCORES_IDENTIFIED_NOT_PROVIDER_CHECKED",
      "frozen_99_provider_candidate_count":total,
      "original_28_prior_provider_and_official_page_concordant_not_independent_official_fixture_id":count_old,
      "additional_published_league_or_club_source_score_observations":count_new,
      "observed_official_or_club_source_total":observed,
      "without_official_or_club_source_research_observation":total-observed,
      "new_score_sources_by_league":groups,
      "new_official_club_source_not_yet_provider_concordant":count_new,
      "separate_source_categories":{
        "ESP1":"La Liga official matchday published scores, match-specific league IDs not captured",
        "NED1":"KNVB official results, provisional until 5 full working days after match",
        "FRA1":"PSG club weekly summary, NOT the official LFP result-ID ledger"},
      "original_4518_data_sha256":DATA_SHA,
      "no_source_supplier_download":True,
      "source_access_budget_not_exceeded":True,
      "official_match_provider_independent_api_attestation_count_new":0,
      "official_match_unique_id_coverage_new":0,
      "production_history_updated":False,"original_seals_updated":False,
      "existing_model_updated":False,"m4_lambdas_recalculated":False,
      "limitations":[
        "This offline code validates recorded canonical team IDs, league season membership, date, scores, evidence URL origin, and bookkeeping; it does NOT fetch official pages itself",
        "Scores from a club weekly report have lower source authority than individual federation fixture records",
        "The new 28 observations were NOT compared to original Football-Data row-level scores, because two light supplier downloads had already been performed this week",
        "The original 28 older comparison scores lack unique federation fixture-ID attestation too",
        "Even with 56 published observations, NONE of the 99 may be silently appended to the accepted 4518-history as newly official-verified match",
        "Without new rights-cleared live 2026-27 event data no reliable pressing or tactical-block input can be created",
      ]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    o=audit(args.root)
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if load(p)!=o:raise EvidenceError("EXISTING_APPEND_ONLY_REPORT_DIFFERS")
    else:p.write_text(json.dumps(o,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":o["status"],"previous":o["original_28_prior_provider_and_official_page_concordant_not_independent_official_fixture_id"],
       "added":o["additional_published_league_or_club_source_score_observations"],
       "unobserved":o["without_official_or_club_source_research_observation"],
       "new_by_league":o["new_score_sources_by_league"]},ensure_ascii=False))

if __name__=="__main__":main()
