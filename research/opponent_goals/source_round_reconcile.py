"""ONE-SHOT second weekly light source read and official matchday score comparison.

The 10 provider CSVs were already downloaded ONCE this week as SHA/count preflight.
This is the second, last allowed light weekly download. It checks:
- byte-for-byte provider SHA matches that first source receipt
- exact old row/date/goals/result anchor and unique provider-name -> canonical ID
- all newly completed candidates with independent manual official league scoreboards
- no silent historic CSV, production M4, original forecasting or sealed-data mutation

Official matchday scores are a human/web research transcription, NOT an automatic
federation API attestation or per-match federation fixture ID; match identity
proof is at league+date+two canonical club IDs. Do not promote directly.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from source_current_one_shot_preflight import (
    read_rows,rows_from_source,parse_day,validate_old_anchor,
    single_fetch,FEEDS,BASE,inspect_feed,
)

SCHEMA="263_TWO_SOURCE_GOAL_CANDIDATES_RESEARCH_ONLY_V1"
OFFICIAL={"TUR1":"www.tff.org","GER1":"www.bundesliga.com","ITA1":"www.legaseriea.it"}
EXPECTED_COUNTS={"TUR1":9,"GER1":9,"ITA1":10}
EXPECTED_TOTAL_PREVIOUS=99

class ReconcileBlocked(ValueError):pass

def verify_ledger(ledger,index,history):
    if ledger.get("schema")!="263_OFFICIAL_MATCHDAY_MANUALLY_OBSERVED_V1" or ledger.get("observed_on_date")!="2026-11-10":
        raise ReconcileBlocked("WRONG_MANUAL_OFFICIAL_EVIDENCE_SCOPE")
    aliases=index.get("aliases",{})
    records=ledger.get("records",[])
    if len(records)!=28:raise ReconcileBlocked("REVIEWED_SCOREBOARD_HAS_WRONG_N")
    expected_fields={"league","date","home_alias","away_alias","home_id","away_id",
                     "home_goals","away_goals","official_week_source","evidence_scope"}
    groups=Counter();seen=set()
    historical_ids={(r["league"],r["match_date"],r["home_id"],r["away_id"]) for r in history}
    for r in records:
        if set(r)!=expected_fields:raise ReconcileBlocked("UNEXPECTED_OFFICIAL_LEDGER_KEYS")
        league=r["league"]
        if league not in OFFICIAL:raise ReconcileBlocked("NON_TARGET_OFFICIAL_LEAGUE")
        url=urlparse(r["official_week_source"])
        if url.scheme!="https" or url.hostname!=OFFICIAL[league] or url.path in ("","/"):
            raise ReconcileBlocked("NOT_ASSOCIATION_OR_LEAGUE_WEB_DOMAIN")
        for side in ("home","away"):
            name=r[f"{side}_alias"]
            if not isinstance(name,str) or aliases.get(name)!=r[f"{side}_id"]:
                raise ReconcileBlocked("OFFICIAL_NAME_TO_CANONICAL_CLUB_ID_NOT_GROUNDED")
        if r["home_id"]==r["away_id"]:raise ReconcileBlocked("SAME_CLUB_BOTH_SIDES")
        d=date.fromisoformat(r["date"])
        if not date(2026,11,6)<=d<=date(2026,11,8):raise ReconcileBlocked("OUTSIDE_OFFICIAL_ROUND")
        if any(type(r[f"{s}_goals"]) is not int or not 0<=r[f"{s}_goals"]<=20
               for s in ("home","away")):
            raise ReconcileBlocked("BAD_OFFICIAL_SCORE")
        if r["evidence_scope"]!="MANUALLY_READ_PUBLIC_OFFICIAL_MATCHDAY_PAGE_2026_11_10":
            raise ReconcileBlocked("OFFICIAL_PAGE_NOT_MACHINE_VERIFIED")
        key=(league,r["date"],r["home_id"],r["away_id"])
        if key in seen:raise ReconcileBlocked("DUPLICATE_OFFICIAL_SCORE")
        if key in historical_ids:raise ReconcileBlocked("RESULT_ALREADY_IN_ACCEPTED_HISTORY")
        seen.add(key);groups[league]+=1
    if dict(groups)!=EXPECTED_COUNTS:raise ReconcileBlocked("NOT_ALL_OFFICIAL_MATCHES_COVERED")
    return { (r["league"],r["date"],r["home_id"],r["away_id"]):r for r in records }

def candidate_index(league,feed,history,name_to_ids):
    cutoff=max(r["match_date"] for r in history if r["league"]==league)
    candidates={};err=Counter()
    for idx,row in feed.items():
        day=parse_day(row.get("Date"))
        if day is None:err["INVALID_FEED_DATE"]+=1;continue
        if day<=cutoff or day>"2026-11-10":continue
        a,b=row.get("FTHG"),row.get("FTAG")
        if a in ("",None) or b in ("",None):continue
        if not (str(a).isdigit() and str(b).isdigit()) or row.get("FTR") not in ("H","D","A"):
            err["INCOMPLETE_OR_CONTRADICTORY_SCORE"]+=1;continue
        aa,bb=int(a),int(b)
        if aa>20 or bb>20 or row["FTR"]!=("H" if aa>bb else "A" if aa<bb else "D"):
            err["INVALID_SCORE_RESULT"]+=1;continue
        hname=str(row.get("HomeTeam","")).strip().casefold()
        aname=str(row.get("AwayTeam","")).strip().casefold()
        hids=name_to_ids.get(hname,set());aids=name_to_ids.get(aname,set())
        if len(hids)!=1 or len(aids)!=1:
            err["CANONICAL_ID_UNRESOLVED"]+=1;continue
        hid=next(iter(hids));aid=next(iter(aids))
        if hid==aid:raise ReconcileBlocked("PROVIDER_BOTH_SIDES_SAME_ID")
        key=(league,day,hid,aid)
        if key in candidates:raise ReconcileBlocked("DUPLICATE_NEW_PROVIDER_FIXTURE")
        candidates[key]={"source_row":idx,"home_goals":aa,"away_goals":bb}
    return candidates,dict(err)

def match_official(official,candidates):
    rows=[];conflicts=[]
    for key,r in sorted(official.items()):
        source=candidates.get(key)
        if source is None:
            conflicts.append({"league":key[0],"date":key[1],"reason":"NO_CANONICAL_PROVIDER_FIXTURE"})
        elif (r["home_goals"],r["away_goals"])!=(source["home_goals"],source["away_goals"]):
            conflicts.append({"league":key[0],"date":key[1],"reason":"OFFICIAL_PROVIDER_FINAL_SCORE_DISAGREEMENT"})
        else:
            rows.append({
                "research_key_sha256":hashlib.sha256("|".join(key).encode("utf8")).hexdigest(),
                "league":key[0],"date":key[1],
                "home_id":key[2],"away_id":key[3],
                "home_goals":r["home_goals"],"away_goals":r["away_goals"],
                "original_provider_row_number":source["source_row"],
                "official_round_url":r["official_week_source"],
                "evidence_status":"MANUAL_OFFICIAL_PAGE_AND_CSV_SCORE_CONCORDANT_NOT_FEDERATION_MATCH_ID_ATTESTED"})
    return rows,conflicts

def audit(root,fetcher=None):
    root=Path(root)
    hist,cols,sha=read_rows(root/"data/quad_accepted_263/extended_history.csv")
    pre=json.loads((root/"research/opponent_goals/reports/current_source_preflight_20261110.json").read_text(encoding="utf8"))
    if pre.get("schema")!="263_20261110_LIGHT_CURRENT_SOURCE_SAFETY_PREFLIGHT_V1" or pre.get("source_4518_sha256")!=sha:
        raise ReconcileBlocked("INVALID_PREVIOUS_ONE_SHOT_SOURCE_PROVENANCE")
    led=json.loads((root/"research/opponent_goals/official_rounds_nov06_08_2026.json").read_text(encoding="utf8"))
    registry=json.loads((root/"experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
    official=verify_ledger(led,registry,hist)
    per={};new_count=0;confirmed=[];conflicts=[];any_source_drift=False
    for league,code in FEEDS.items():
        previous=pre["leagues"].get(league,{})
        try:
            url=BASE+code+".csv"
            # Exactly one network GET per league. No retry on source error.
            blob=fetcher(url) if fetcher else single_fetch(url)
            if type(blob) is not bytes or not blob:raise ReconcileBlocked("BAD_SOURCE_BYTES")
            fetched_sha=hashlib.sha256(blob).hexdigest()
            if fetched_sha!=previous.get("provider_payload_sha256"):
                any_source_drift=True
                per[league]={"status":"BLOCKED_SOURCE_SHA_CHANGED","previous_sha":previous.get("provider_payload_sha256"),"new_sha":fetched_sha}
                continue
            feed=rows_from_source(blob)
            safe,anchored,total,fail,names=validate_old_anchor(league,code,feed,hist)
            if not safe or anchored!=previous.get("historical_exact_row_score_date_anchors"):
                per[league]={"status":"BLOCKED_HISTORY_ANCHOR_OR_ID_CHANGED",
                    "anchored":anchored,"expected_old":total,"rejections":fail}
                continue
            candidates,err=candidate_index(league,feed,hist,names)
            prev_count=previous.get("newer_completed_score_rows_candidate_count")
            if len(candidates)!=prev_count:
                per[league]={"status":"BLOCKED_NEW_CANDIDATE_COUNT_OR_ID_CONFLICT",
                    "accepted_id_candidates":len(candidates),"previous_count":prev_count,
                    "reject_summary":err}
                continue
            subset={key:value for key,value in official.items() if key[0]==league}
            confirmed_league,mismatches=match_official(subset,candidates)
            if mismatches:
                conflicts.extend(mismatches)
                per[league]={"status":"OFFICIAL_PROVIDER_CONFLICT_HOLD",
                     "new_provisional":len(candidates),"official_matched":len(confirmed_league),
                     "conflict_count":len(mismatches)}
                continue
            confirmed.extend(confirmed_league)
            new_count+=len(candidates)
            per[league]={"status":"SOURCE_SHA_AND_CANONICAL_ID_MATCHED",
                "original_old_source_anchor_count":anchored,
                "new_provisional":len(candidates),"official_matched":len(confirmed_league),
                "independent_official_not_compared_count":len(candidates)-len(confirmed_league),
                "provider_sha256":fetched_sha,"reject_summary":err}
        except Exception as e:
            per[league]={"status":"SOURCE_BLOCKED_NO_RETRY","reason":type(e).__name__}
    all_ok=(all(x.get("status")=="SOURCE_SHA_AND_CANONICAL_ID_MATCHED" for x in per.values())
            and new_count==EXPECTED_TOTAL_PREVIOUS and len(confirmed)==len(official)
            and not conflicts and not any_source_drift)
    return {
       "schema":SCHEMA,
       "status":"RESEARCH_MATCHED_OFFICIAL_ROUNDS_NOT_OFFICIAL_MATCH_ID_ATTESTED" if all_ok else "RESEARCH_HOLD_FAILED_SOURCE_OR_OFFICIAL_JOIN",
       "source_snapshot_sha256":sha,
       "first_light_fetch_receipt":"research/opponent_goals/reports/current_source_preflight_20261110.json",
       "second_light_fetch_2026_11_10":True,
       "no_more_same_week_supplier_downloads":True,
       "manually_read_official_rounds":28,
       "provider_new_candidates_total":new_count if all_ok else None,
       "official_provider_concordant_count":len(confirmed),
       "provisional_not_officially_checked_count":new_count-len(confirmed) if all_ok else None,
       "per_league":per,
       "score_conflicts":conflicts,
       "officially_read_results_with_provider_concordance":confirmed,
       "limitations":[
          "Independent official website data was manually observed by research, not machine re-fetched or locked by match ID",
          "The federation/league per-match fixture ID is not yet matched to provider data; official result attestation remains PENDING",
          "None of these 28 match outcomes is silently appended to the accepted 4518-match source or production 2.6.3",
          "The other 71 are PROVISIONAL candidate counts only and cannot be called accepted matches",
          "Identical old source scores+row index anchor the mapping, but this is not official federation identity proof",
          "No automatic calibration or M4 probability modification is allowed",
          "Football-Data permits at most light twice-weekly personal/academic access; this second run exhausts the budget",
       ],
       "accepted_history_modified":False,"model_or_predictions_modified":False,"official_score_archive_updated":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    path=Path(a.out)
    if path.exists():raise ReconcileBlocked("SOURCE_SECOND_DOWNLOAD_HAS_ALREADY_RUN_REPORT_EXISTS")
    report=audit(a.root)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({k:report[k] for k in (
        "status","manually_read_official_rounds","provider_new_candidates_total",
        "official_provider_concordant_count","provisional_not_officially_checked_count",
        "per_league")},ensure_ascii=False),flush=True)

if __name__=="__main__":main()
