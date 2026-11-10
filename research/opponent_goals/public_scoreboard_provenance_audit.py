"""Audit three independently labeled result-evidence tiers, without new downloads.

28 league/federation public results have source+provider agreement from prior
separate research; 28 newer public scores have NO source-row rejoin. Never
promote either tier to federation fixture-ID attestation automatically.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_NEW={"ESP1":("www.laliga.com","LEAGUE_DIRECT_SCOREBOARD_WITHOUT_FIXTURE_ID",10),
             "NED1":("www.knvb.nl","FEDERATION_DIRECT_SCOREBOARD_WITHOUT_FIXTURE_ID",9),
             "FRA1":("www.psg.fr","CLUB_PUBLISHED_FULL_MATCHDAY_RECAP_NOT_FEDERATION",9)}
ALLOWED_OLD={"TUR1":9,"GER1":9,"ITA1":10}
STATUS="PUBLIC_WEB_PAGE_SCORE_NOT_PROVIDER_SHA_REJOINED"

class ProvenanceBlocked(ValueError):pass

def check(root):
    root=Path(root)
    idx=json.loads((root/"experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
    old=json.loads((root/"research/opponent_goals/official_rounds_nov06_08_2026.json").read_text(encoding="utf8"))
    new=json.loads((root/"research/opponent_goals/public_matchday_28_more_20261110.json").read_text(encoding="utf8"))
    rec=json.loads((root/"research/opponent_goals/reports/official_round_score_concordance_20261110.json").read_text(encoding="utf8"))
    pre=json.loads((root/"research/opponent_goals/reports/current_source_preflight_20261110.json").read_text(encoding="utf8"))
    if old.get("schema")!="263_OFFICIAL_MATCHDAY_MANUALLY_OBSERVED_V1" or len(old.get("records",[]))!=28:
        raise ProvenanceBlocked("ORIGINAL_28_LEDGER_MISMATCH")
    if new.get("schema")!="263_PUBLIC_SCOREBOARD_WEB_OBSERVED_CANONICAL_28_V1" or new.get("observed_on_date")!="2026-11-10" or len(new.get("records",[]))!=28:
        raise ProvenanceBlocked("ADDITIONAL_PUBLIC_28_SCHEMA_MISMATCH")
    if rec.get("official_provider_concordant_count")!=28 or len(rec.get("score_conflicts",[])) or rec.get("provider_new_candidates_total")!=99:
        raise ProvenanceBlocked("ORIGINAL_28_PROVIDER_REPORT_NOT_CONFIRMED")
    if pre.get("schema")!="263_20261110_LIGHT_CURRENT_SOURCE_SAFETY_PREFLIGHT_V1":
        raise ProvenanceBlocked("PREVIOUS_SOURCE_ATTESTATION_MISSING")
    aliases=idx["aliases"]
    count=Counter();by_tier=Counter();seen=set()
    historical,_,_=__import__("data_opponent_goal_audit").read_rows(root/"data/quad_accepted_263/extended_history.csv")
    old_keys={(r["league"],r["match_date"],r["home_id"],r["away_id"]) for r in historical}
    for row in new["records"]:
        league=row.get("league")
        if league not in ALLOWED_NEW:raise ProvenanceBlocked("NON_TARGET_LEAGUE_IN_NEW_PUBLIC_SET")
        domain,tier,expected=ALLOWED_NEW[league]
        u=urlparse(row.get("source_url",""))
        if u.scheme!="https" or u.netloc!=domain or not u.path or row.get("source_tier")!=tier:
            raise ProvenanceBlocked("UNAPPROVED_PUBLIC_SOURCE_TIER")
        if row.get("status")!=STATUS:raise ProvenanceBlocked("NEW_SCORE_HAS_UNSUPPORTED_AUTHORITY_STATUS")
        if (aliases.get(row.get("home_alias"))!=row.get("home_id") or
            aliases.get(row.get("away_alias"))!=row.get("away_id") or
            row.get("home_id")==row.get("away_id")):
            raise ProvenanceBlocked("CANONICAL_CLUB_ID_NOT_REGISTRY_GROUNDED")
        d=date.fromisoformat(row["date"])
        if d<date(2026,11,6) or d>date(2026,11,8):raise ProvenanceBlocked("PUBLIC_RESULT_NOT_IN_NOV_WINDOW")
        h,a=row.get("home_goals"),row.get("away_goals")
        if type(h)!=int or type(a)!=int or not (0<=h<=20 and 0<=a<=20):
            raise ProvenanceBlocked("INVALID_PUBLIC_SCORE")
        key=(league,row["date"],row["home_id"],row["away_id"])
        if key in old_keys or key in seen:raise ProvenanceBlocked("DUPLICATE_OR_ALREADY_ACCEPTED_SCORE")
        seen.add(key);count[league]+=1;by_tier[tier]+=1
    for league,(dom,tier,expected) in ALLOWED_NEW.items():
        if count[league]!=expected:raise ProvenanceBlocked("MISSING_SCOREBOARD_FIXTURE")
        if pre["leagues"][league]["newer_completed_score_rows_candidate_count"]!=expected:
            raise ProvenanceBlocked("PUBLIC_SCORE_COUNT_DIFFERS_FROM_PREVIOUS_SOURCE_2016_27")
    old_seen=set()
    old_counts=Counter()
    for row in old["records"]:
        key=(row["league"],row["date"],row["home_id"],row["away_id"])
        if key in old_seen or key in seen:raise ProvenanceBlocked("DUPLICATE_BETWEEN_TWO_EVIDENCE_LAYERS")
        old_seen.add(key);old_counts[row["league"]]+=1
    if dict(old_counts)!=ALLOWED_OLD:raise ProvenanceBlocked("OLD_28_COUNTS_MISMATCH")
    hashes=sorted(hashlib.sha256("|".join(k).encode()).hexdigest() for k in seen)
    return {"schema":"263_OFFICIAL_RESULT_EVIDENCE_LAYERS_AUDIT_20261110_V1",
      "status":"SOURCE_TIERS_SEPARATED_NOT_PROMOTED_TO_ACCEPTED_HISTORY",
      "candidate_total":rec["provider_new_candidates_total"],
      "provider_official_scoreboard_concordant_28":len(old_seen),
      "additional_public_scoreboard_only":len(seen),
      "public_direct_league_or_federation_without_provider_match":sum(by_tier[t] for t in by_tier if "CLUB" not in t),
      "public_club_recap_without_provider_match":by_tier["CLUB_PUBLISHED_FULL_MATCHDAY_RECAP_NOT_FEDERATION"],
      "remaining_candidate_league_counts_without_public_web_capture":rec["provider_new_candidates_total"]-len(old_seen)-len(seen),
      "pending_provider_crosscheck_of_additional_public_results":len(seen),
      "pending_provider_plus_public_per_fixture_match_count":rec["provider_new_candidates_total"]-len(old_seen),
      "additional_public_team_date_id_hashes":hashes,
      "by_evidence_class_counts":dict(by_tier),
      "old_score_28_matches_federation_id_verified":False,
      "new_28_same_supplier_row_rejoined":False,
      "new_28_federation_id_verified":False,
      "accepted_new_history_rows":0,
      "license_assumptions_or_raw_data_downloads":False,
      "production_263_probabilities_or_m4_modified":False,
      "limitations":[
          "Count equality by league alone does not prove 28 new public scores correspond to specific supplier source rows",
          "Previous 28 are public-official-round + independently fetched provider CSV score agreements, not federation fixture-ID attestations",
          "New 19 ESP/NED are league/federation public scoreboards but lack provider source-row join",
          "New 9 FRA use PSG club's recap of a full Ligue1 round, not the Ligue1 federation result source",
          "Remaining 43 is an unaccounted-by-this-manual-capture count, not a proven missing score on a federation website",
          "No more Football-Data GET this week; do not mutate model, accepted source, seals, or official postmatch directory"]}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",default=".")
    a.add_argument("--out",required=True)
    args=a.parse_args()
    data=check(args.root)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        if json.loads(out.read_text(encoding="utf8"))!=data:
            raise ProvenanceBlocked("IMMUTABLE_AUDIT_CONFLICT")
    else:out.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:data[k] for k in ("status","candidate_total","provider_official_scoreboard_concordant_28","additional_public_scoreboard_only","remaining_candidate_league_counts_without_public_web_capture")},ensure_ascii=False))

if __name__=="__main__":main()
