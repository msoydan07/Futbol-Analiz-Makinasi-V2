"""Read-only 4518 accepted vs 4617 staged vs 99 independently recorded published scores.

Stage is from existing GitHub experiment branch, NOT fresh provider download.
The latest staged audit explicitly says its provider fetch is UNVERIFIED.
This integrity audit cannot attest official league fixture IDs, data license,
or pregame model capability. Never change canonical data or sealed results.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ACCEPTED_SHA="1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9"
STAGED_SHA="7f005d88465fa742354854a0459f06fbb17efe9fbb648e26a18844d0f7753958"
SOURCE_MAP={"ENG1":"E0","ENG2":"E1","GER1":"D1","ESP1":"SP1","ITA1":"I1",
            "FRA1":"F1","NED1":"N1","TUR1":"T1","POR1":"P1","BEL1":"B1"}
FIELDS=("fixture_id","league","season","match_date","home_id","away_id","home_goals",
"away_goals","result","source_row","source_url")
class AuditStop(ValueError):pass

def enforce(ok,label):
    if not ok:raise AuditStop(label)

def load_csv(path,expected_sha):
    data=Path(path).read_bytes()
    enforce(hashlib.sha256(data).hexdigest()==expected_sha,"EXPECTED_SOURCE_SHA_MISMATCH")
    import io
    reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    enforce(set(FIELDS).issubset(reader.fieldnames or []),"CSV_SCHEMA_MISMATCH")
    rows=list(reader)
    enforce(all(None not in r for r in rows),"MALFORMED_CSV_EXTRA_COLUMNS")
    enforce(len({r["fixture_id"] for r in rows})==len(rows),"DUPLICATE_SOURCE_FIXTURE_ID")
    return rows

def key(row):
    return (row["league"],row["match_date"],row["home_id"],row["away_id"])

def validate_source_identity(row):
    league=row["league"]
    enforce(league in SOURCE_MAP,"UNEXPECTED_LEAGUE")
    enforce(row["season"]=="2026-2027","UNEXPECTED_NEW_SEASON")
    enforce(row["source_url"]==f"https://www.football-data.co.uk/mmz4281/2627/{SOURCE_MAP[league]}.csv",
            "SOURCE_URL_WRONG_LEAGUE_OR_SEASON")
    enforce(row["source_row"].isdigit() and int(row["source_row"])>=2,
            "SOURCE_ROW_ID_NOT_NUMERIC")
    h,a=int(row["home_goals"]),int(row["away_goals"])
    enforce(0<=h<=20 and 0<=a<=20 and
        row["result"]==("H" if h>a else "A" if h<a else "D"),
        "STAGED_SCORE_INCONSISTENT")

def evidence_99(root):
    root=Path(root)
    old=json.loads((root/"research/opponent_goals/official_rounds_nov06_08_2026.json").read_text(encoding="utf8"))
    mid=json.loads((root/"research/opponent_goals/public_matchday_28_more_20261110.json").read_text(encoding="utf8"))
    last=json.loads((root/"research/opponent_goals/remaining_43_public_score_observations_20261110.json").read_text(encoding="utf8"))
    enforce(len(old["records"])==28 and len(mid["records"])==28 and len(last["records"])==43,
           "INCOMPLETE_EVIDENCE_99")
    out={}
    for tier,arr in (
        ("28_PRIOR_OFFICIAL_SCORE_AND_PROVIDER_CONCORDANCE",old["records"]),
        ("28_OFFICIAL_OR_CLUB_PUBLIC_SOURCE_NO_PROVIDER_JOIN",mid["records"]),
        ("43_EXTERNAL_SCORE_WITH_OFFICIAL_FIXTURE_PARTIAL",last["records"])
    ):
        for x in arr:
            lookup=(x["league"],x.get("date") or x.get("match_date"),x["home_id"],x["away_id"])
            enforce(lookup[1] and lookup not in out,"DUPLICATE_PUBLISHED_FIXTURE")
            out[lookup]=dict(home_goals=int(x["home_goals"]),away_goals=int(x["away_goals"]),
                             source_tier=tier)
    enforce(len(out)==99,"RESEARCH_99_NOT_COMPLETE")
    return out

def compare(root,staged_file):
    root=Path(root)
    accepted=load_csv(root/"data/quad_accepted_263/extended_history.csv",ACCEPTED_SHA)
    staged=load_csv(staged_file,STAGED_SHA)
    enforce(len(accepted)==4518 and len(staged)==4617,"UNEXPECTED_HISTORY_SIZES")
    acc_by_id={r["fixture_id"]:r for r in accepted}
    stage_by_id={r["fixture_id"]:r for r in staged}
    missing_original=set(acc_by_id)-set(stage_by_id)
    old_modified=sum(acc_by_id[k]!=stage_by_id[k] for k in acc_by_id.keys()&stage_by_id.keys())
    # Report conflicts even if old archive cannot be accepted; never silently drop.
    new=[r for k,r in stage_by_id.items() if k not in acc_by_id]
    accepted_keys={key(r) for r in accepted}
    stage_keys={key(r) for r in staged}
    enforce(len(stage_keys)==len(staged),"STAGED_DUPLICATE_CANONICAL_FIXTURE_KEY")
    enforce(len(accepted_keys)==len(accepted),"ACCEPTED_DUPLICATE_CANONICAL_FIXTURE_KEY")
    ledger=evidence_99(root)
    new_keys={key(r) for r in new}
    row_key_overlap=new_keys&accepted_keys
    score_conflicts=[]
    missing_from_stage=sorted(set(ledger)-new_keys)
    unexplained_stage=sorted(new_keys-set(ledger))
    by=defaultdict(lambda:{"new":0,"score_matches":0,"score_conflicts":0,"published_tier_counts":Counter()})
    seen_source_rows=set()
    for row in new:
        validate_source_identity(row)
        src_key=(row["league"],row["season"],row["source_url"],row["source_row"])
        enforce(src_key not in seen_source_rows,"DUPLICATE_NEW_PROVIDER_ROW_INDEX")
        seen_source_rows.add(src_key)
        b=by[row["league"]];b["new"]+=1
        ref=ledger.get(key(row))
        if ref:
            b["published_tier_counts"][ref["source_tier"]]+=1
            if (int(row["home_goals"]),int(row["away_goals"]))==(ref["home_goals"],ref["away_goals"]):
                b["score_matches"]+=1
            else:
                b["score_conflicts"]+=1
                score_conflicts.append({
                  "league":row["league"],
                  "match_key_sha256":hashlib.sha256("|".join(key(row)).encode("utf8")).hexdigest(),
                  "staged_score":[int(row["home_goals"]),int(row["away_goals"])],
                  "published_score":[ref["home_goals"],ref["away_goals"]],
                  "source_tier":ref["source_tier"]
                })
    intact=(not missing_original and not old_modified and len(new)==99
            and len(stage_keys)==4617 and not row_key_overlap)
    complete=(intact and not missing_from_stage and not unexplained_stage and not score_conflicts)
    # This classifies as staged/observed concordance, never official match-ID approval.
    return {
      "schema":"263_ACCEPTED4518_STAGED4617_PUBLIC99_INTEGRITY_GATE_V1",
      "status":"COMPLETE_STAGED_99_SCORE_AGREEMENT_NO_OFFICIAL_ID" if complete
               else "HOLD_STAGE_CONFLICT_OR_MISSING_RECORD",
      "accepted_4518_sha256":ACCEPTED_SHA,"staged_4617_sha256":STAGED_SHA,
      "accepted_n":len(accepted),"staged_n":len(staged),
      "accepted_original_missing_in_staged_count":len(missing_original),
      "accepted_original_modified_in_staged_count":old_modified,
      "new_staged_fixture_id_count":len(new),
      "new_staged_key_overlaps_old_count":len(row_key_overlap),
      "preexisting_evidence_total":len(ledger),
      "published_evidence_missing_from_staged_n":len(missing_from_stage),
      "unexplained_staged_new_records_n":len(unexplained_stage),
      "staged_vs_published_score_disagreements":score_conflicts,
      "matches_by_league":{k:{**{j:v for j,v in value.items() if j!="published_tier_counts"},
                             "published_tier_counts":dict(value["published_tier_counts"])}
                           for k,value in sorted(by.items())},
      "stage_experiment_branch_provider_fetch_independently_verified":False,
      "official_unique_fixture_id_attestations_new":0,
      "source_license_verified_for_reuse":False,
      "not_an_independent_published_score_validation":True,
      "all_99_have_published_scores_but_provenance_varies":True,
      "promote_to_accepted_history":False,
      "production_M4_untouched":True,
      "sealed_forecasts_untouched":True,
      "limitations":[
       "Existing GitHub staged CSV derived from owner pipeline; its audit records provider_fetch_independently_verified=false",
       "Published web score ledger records have mixed primary, club and secondary provenance",
       "Matching staged scores to those ledgers is NOT matching official federation's canonical per-fixture ID",
       "League+date+canonical teams are known but provider-source-row provenance and usage rights still need assessment",
       "The previous Tuesday stage rows and 99 candidate public score observations all represent retrospective outcomes",
       "No model training, calibration, historic append or daily forecast update was made",
       "A status of COMPLETE indicates data consistency across stored copies, not that source scores are true",
      ]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--staged",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    obj=compare(args.root,args.staged)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        old=json.loads(out.read_text(encoding="utf8"))
        enforce(old==obj,"APPEND_ONLY_REPORT_DIFFERS")
    else:out.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"status":obj["status"],
       "original_missing":obj["accepted_original_missing_in_staged_count"],
       "original_changed":obj["accepted_original_modified_in_staged_count"],
       "new_staged_count":obj["new_staged_fixture_id_count"],
       "research_99_missing":obj["published_evidence_missing_from_staged_n"],
       "unexplained_stage":obj["unexplained_staged_new_records_n"],
       "score_disagreements":len(obj["staged_vs_published_score_disagreements"]),
       "per_league":obj["matches_by_league"]},ensure_ascii=False))
if __name__=="__main__":main()
