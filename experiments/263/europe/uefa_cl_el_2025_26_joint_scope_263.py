"""2025/26 CL+EL, same season: read-only ten-league identity coverage audit.
Public non-UEFA feed is verified by six official result samples, not every match.
No model training, no fixture lookup, no domestic file modification.
"""
import collections,hashlib,json
from pathlib import Path
from uefa_tactical_study_263 import fetch_pinned_source,parse_league_phase,validate_source_rows
from uefa_strength_source_audit_263 import split_uefa_club,validate_index
from uefa_ten_league_scope_gate_263 import norm
from uefa_el_2025_26_scope_source_263 import fetch_public_feed,decode_feed,referenced_alias

OUT=Path("data/europe_staged_263/cl_el_2025_26_scope")
def check(rows_cl,rows_el,index):
    validate_index(index)
    allowed=set().union(*index["season_memberships"]["2025-2026"].values())
    counts={};selected=[];seen={}
    for cup,rows in (("CL",rows_cl),("EL",rows_el)):
        reasons=collections.Counter();clubs=set()
        for r in rows:
            names=([split_uefa_club(r[k])[0] for k in ("home","away")]
                   if cup=="CL" else [r[k] for k in ("home","away")])
            ids=[referenced_alias(name,index)[0] for name in names]
            if any(x is None for x in ids):
                reasons["UNKNOWN_NAME_EXCLUDED"]+=1
                continue
            if any(x not in allowed for x in ids):
                reasons["OUTSIDE_2025_26_TEN_LEAGUES_EXCLUDED"]+=1
                continue
            if ids[0]==ids[1]:raise ValueError("CLUB_ID_COLLISION")
            reasons["TWO_IN_SCOPE_CANDIDATES"]+=1
            clubs.update(ids)
            selected.append({"cup":cup,"date":r["date"],"home_candidate":ids[0],
                "away_candidate":ids[1],"home_name":r["home"],"away_name":r["away"],
                "home_goals":r.get("hg",r.get("home_goals")),
                "away_goals":r.get("ag",r.get("away_goals")),
                "club_identity_officially_verified":False,"model_eligible":False})
        counts[cup]={"all":len(rows),"candidates":reasons["TWO_IN_SCOPE_CANDIDATES"],
                     "excluded":len(rows)-reasons["TWO_IN_SCOPE_CANDIDATES"],
                     "reasons":dict(reasons)}
        seen[cup]=clubs
    report={"schema":"263_CL_EL_2025_26_COVERAGE_REVIEW_V1",
        "season":"2025-2026","coverage":counts,
        "selected_name_candidates":len(selected),
        "distinct_candidate_clubs_per_competition":{k:len(v) for k,v in seen.items()},
        "shared_clubs_between_competitions":len(seen["CL"]&seen["EL"]),
        "official_uefa_club_id_links_verified":0,
        "complete_matchwise_official_verification":False,
        "historical_domestic_strength_asof_match_verified":False,
        "can_train_strength_model":False,"main_or_pilot_changed":False,
        "2024_25_season_membership_inferred":False}
    return report,selected
def run():
    index=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf8"))
    cl_bytes,cl_url=fetch_pinned_source("2025-26/cl.txt")
    cl=parse_league_phase(cl_bytes,"UEFA_CL","2025-2026")
    validate_source_rows(cl,"UEFA_CL","2025-2026",144,487)
    el_bytes=fetch_public_feed()
    el=decode_feed(el_bytes)
    report,selected=check(cl,el,index)
    report["source_sha256"]={"cl":hashlib.sha256(cl_bytes).hexdigest(),
                             "el":hashlib.sha256(el_bytes).hexdigest()}
    report["source_urls"]={"cl":cl_url,"el":"https://fixturedownload.com/feed/json/europa-league-2025"}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"scope_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (OUT/"review_only_matches.json").write_text(json.dumps({"training_allowed":False,
       "matches":selected},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("JOINT_SCOPE="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":run()
