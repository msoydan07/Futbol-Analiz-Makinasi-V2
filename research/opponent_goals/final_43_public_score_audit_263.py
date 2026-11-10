"""One-pass independently tiered source-ledger and score integrity audit.

The result does NOT assert official federation fixture identity or evidence
of accepted training data. No external requests, no 3rd Football-Data pull;
original M4 and historical SHA remain unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from collections import Counter,defaultdict
from datetime import date
from urllib.parse import urlparse

SOURCE_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
COUNTS={"ENG1":10,"ENG2":15,"BEL1":10,"POR1":8}
SOURCES={
  "ENG1":("radarfooty.com","www.premierleague.com","SECONDARY_ROUND_SCORES_OFFICIAL_LEAGUE_FIXTURES_PARTIAL_OFFICIAL_SCORE_ARTICLES"),
  "ENG2":("www.skysports.com","www.efl.com","BROADCASTER_SCORES_EFL_PARTIAL_SCORE_ARTICLE"),
  "BEL1":("www.footballwebpages.co.uk","datencenter.dfb.de","SECONDARY_SCORES_FOREIGN_FEDERATION_CROSSCHECK_ROUND11_EXCEPT_NOV04"),
  "POR1":("egolo.pt","www.ligaportugal.pt","SECONDARY_SCORES_OFFICIAL_LEAGUE_FIXTURE_SCHEDULE"),
}
class Blocked(ValueError):pass
def ensure(c,why):
    if not c:raise Blocked(why)
def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))
def fixture_key(r):
    return (r["league"],r["date"],r["home_id"],r["away_id"])
def check_43(data,index,keys_seen,history):
    ensure(data.get("schema")=="263_20261110_LAST43_EXTERNAL_REPORTED_SCORES_NOT_OFFICIAL_FEDERATION_ATTESTATION_V1","INVALID_LAST43_SCOPE")
    ensure(data.get("date_cutoff")=="2026-11-10" and data.get("supplier_downloaded") is False,"NETWORK_ACCESS_UNAUTHORIZED")
    ensure(data.get("official_match_id_attested_count") == 0 and data.get("model_or_history_changed") is False,"UNFOUNDED_OFFICIAL_STATUS")
    rows=data["records"]
    ensure(type(rows)==list and len(rows)==43,"EXPECTED_43_ADDITIONAL_SCORES")
    members=index["season_memberships"]["2026-2027"]
    aliases=index["aliases"]
    by=Counter()
    for r in rows:
        ensure(r.get("league") in COUNTS,"UNKNOWN_LEAGUE")
        league=r["league"]
        ensure(set(r)=={"league","date","home_id","away_id","home_alias","away_alias",
                       "home_goals","away_goals","result","published_score_url","complementary_url",
                       "evidence_tier","official_fixture_id","provider_row_linked",
                       "score_class","recorded_utc_cutoff"},"ADDITIONAL_ROW_SCHEMA_CHANGED")
        a,b,t=SOURCES[league]
        for url,host in ((r["published_score_url"],a),(r["complementary_url"],b)):
            uri=urlparse(url)
            ensure(uri.scheme=="https" and uri.hostname==host and uri.path and uri.path!="/","UNTRUSTED_SCORE_SOURCE")
        ensure(r["evidence_tier"]==t,"EXAGGERATED_EVIDENCE_TIER")
        ensure(r["provider_row_linked"] is False and r["official_fixture_id"] is None,"UNVERIFIED_LINK_PROMOTED_TO_OFFICIAL")
        ensure(r["score_class"]=="EXTERNAL_PUBLIC_REPORT_NOT_FEDERATION_ID_ATTESTED","UNSUPPORTED_OFFICIAL_ATTESTATION")
        ensure(r["recorded_utc_cutoff"]=="2026-11-10","SCORE_FROM_FUTURE_SOURCE")
        ensure(date(2026,11,4)<=date.fromisoformat(r["date"])<=date(2026,11,8),"OUTSIDE_NOV4_8")
        for side in ("home","away"):
            ensure(aliases.get(r[side+"_alias"])==r[side+"_id"],"IDENTITY_ALIAS_WRONG")
            ensure(r[side+"_id"] in members[league],"WRONG_SEASON_CLUB")
        ensure(r["home_id"]!=r["away_id"],"SAME_TEAM_BOTH_SIDES")
        h,away=r["home_goals"],r["away_goals"]
        ensure(type(h)==int and type(away)==int and 0<=h<=20 and 0<=away<=20,"INVALID_FINAL_SCORE")
        ensure(r["result"]==("H" if h>away else "A" if h<away else "D"),"FINAL_SCORE_RESULT_DISAGREE")
        key=fixture_key(r)
        ensure(key not in keys_seen and key not in history,"DUPLICATED_IN_PRIOR_LEDGER_OR_HISTORY")
        keys_seen.add(key);by[league]+=1
    ensure(dict(by)==COUNTS,"WRONG_LEAGUE_TOTAL")
    portugal= [r for r in rows if r["league"]=="POR1"]
    ensure(len(portugal)==8 and not any(
        {r["home_alias"],r["away_alias"]}=={"estoril","maritimo"} for r in portugal),
        "POSTPONED_PORTUGAL_FIXTURE_MUST_NOT_HAVE_RESULT")
    return by

def run(root):
    root=Path(root)
    source=root/"data/quad_accepted_263/extended_history.csv"
    raw=source.read_bytes()
    ensure(hashlib.sha256(raw).hexdigest()==SOURCE_SHA,"ACCEPTED_ORIGINAL_HISTORY_CHANGED")
    import csv,io
    old_history=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    ensure(len(old_history)==4518,"ORIGINAL_HISTORY_ROW_COUNT")
    past={(r["league"],r["match_date"],r["home_id"],r["away_id"]) for r in old_history}
    idx=read(root/"experiments/263/evidence/identity_index_263.json")
    old=read(root/"research/opponent_goals/official_rounds_nov06_08_2026.json")
    mid=read(root/"research/opponent_goals/public_matchday_28_more_20261110.json")
    score=read(root/"research/opponent_goals/reports/official_round_score_concordance_20261110.json")
    layer=read(root/"research/opponent_goals/reports/official_public_evidence_layers_20261110.json")
    last=read(root/"research/opponent_goals/remaining_43_public_score_observations_20261110.json")
    ensure(score["status"]=="RESEARCH_MATCHED_OFFICIAL_ROUNDS_NOT_OFFICIAL_MATCH_ID_ATTESTED" and
        score["provider_new_candidates_total"]==99 and
        score["official_provider_concordant_count"]==28 and score["score_conflicts"]==[],
        "SOURCE_PROVIDER_PRIOR_RECEIPT_INCONSISTENT")
    ensure(layer["provider_official_scoreboard_concordant_28"]==28 and
           layer["additional_public_scoreboard_only"]==28 and
           layer["accepted_new_history_rows"]==0,"PREVIOUS_56_EVIDENCE_CHANGED")
    ensure(len(old["records"])==28 and len(mid["records"])==28,"PREVIOUS_LEDGER_COUNT")
    seen=set()
    for item in old["records"]:
        key=fixture_key(item)
        ensure(key not in past and key not in seen,"ORIGINAL_28_NOT_NEW_OR_DUPLICATED")
        seen.add(key)
    for item in mid["records"]:
        key=fixture_key(item)
        ensure(key not in past and key not in seen,"ADDITIONAL_28_NOT_NEW_OR_DUPLICATED")
        seen.add(key)
    by=check_43(last,idx,seen,past)
    ensure(len(seen)==99,"ALL_99_NOT_COVERED")
    rows=last["records"]
    result={}
    for league in COUNTS:
        sub=[r for r in rows if r["league"]==league]
        result[league]={
          "external_published_score_observations":len(sub),
          "historical_provider_row_rejoined":0,
          "official_federation_match_id_attested":0,
          "observed_btts_count":sum(r["home_goals"]>0 and r["away_goals"]>0 for r in sub),
          "observed_over25_count":sum(r["home_goals"]+r["away_goals"]>=3 for r in sub),
          "source_tier":SOURCES[league][2]}
    return {
      "schema":"263_LAST43_PUBLIC_SCORE_IDENTITY_UNCERTAINTY_AUDIT_V1",
      "decision":"99_OF_99_PUBLISHED_SCORE_OBSERVATIONS_RECORDED_BUT_NO_MODEL_ACCEPTANCE",
      "accepted_training_history_n":4518,
      "frozen_original_history_sha256":SOURCE_SHA,
      "previous_official_or_league_score_provider_concordance_n":28,
      "previous_published_official_league_or_club_only_n":28,
      "last_external_published_scores_n":43,
      "total_score_observations":99,
      "all_99_canonical_team_date_home_away_keys_unique":True,
      "new_43_provider_row_matches":0,
      "total_newly_accepted_provider_rows":0,
      "total_new_federation_unique_fixture_ids_attested":0,
      "historical_score_archive_modified":False,
      "models_or_forecasts_changed":False,
      "football_data_access_repeated":False,
      "portugal_postponed_estoril_maritimo_not_scored":True,
      "league_detail":result,
      "limitations":[
        "Original 28 have official round and provider independently observed same results, but lack federation match-ID attestation",
        "Second 28 have published league/federation/club source score observations, but have not been reconciled to provider source rows",
        "Final 43 have published score observations, with secondary or partly official support; they lack independent provider row reconciliation and local federation game-ID attestation",
        "The public source webpages are not fetched by GitHub QA, which validates ONLY the manually transcribed records and their known source domains",
        "Raw third-party result rows or fixture IDs were not downloaded; 99 public scores do not automatically constitute rights-cleared accepted CSV records",
        "These 99 are all after current 4518 archive's latest date per league; they are NOT eligible for prior already sealed pre-match predictions",
        "This is not a new 99-game forward model accuracy pilot",
        "Do not calculate or adjust M4/KG/Over percentages from these unaccepted records",
      ]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=run(args.root)
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if read(target)!=out:raise Blocked("APPEND_ONLY_REPORT_MISMATCH")
    else:target.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"decision":out["decision"],"total":out["total_score_observations"],"new_last43":out["last_external_published_scores_n"],"by_league":out["league_detail"]},ensure_ascii=False))
if __name__=="__main__":main()
