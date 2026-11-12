"""Read a ONE-TIME Nov8 result archive instead of endlessly fetching old scores.

Research evidence is not fraudulently promoted to human/federation attestation.
Every result must match original immutable pre-kickoff SHA + original web review.
Only the exact Nov8 cohort is cached; future cohorts retain live source checks.
"""
import json
from pathlib import Path
from collections import defaultdict

REL="data/results_only_263/nov8_new100_terminal_archive_20261112.json"
SCHEMA="263_NOV8_NEW100_POSTMATCH_TERMINAL_ARCHIVE_V1"
TFF={"Çaykur Rizespor":"317877","Çorum FK":"317879","Beşiktaş":"317881"}
EXPECTED={"TFF_NETWORK_VERIFIED":3,"OFFICIAL_CLUB_WEB_RESEARCH":13,
          "OFFICIAL_LEAGUE_WEB_RESEARCH":22,"EXTERNAL_FEDERATION_WEB_RESEARCH":1,
          "POSTPONED_UNSCORED":1}

class ArchiveRejected(ValueError):pass

def checked(root,forecasts,named,doc=None):
    root=Path(root)
    d=json.loads((root/REL).read_text(encoding="utf-8")) if doc is None else doc
    if (d.get("schema")!=SCHEMA or d.get("cohort")!="new100"
        or d.get("match_date")!="2026-11-08" or
        (d.get("registered"),d.get("completed"),d.get("postponed"))!=(40,39,1)
        or d.get("official_tff_network_verified")!=3
        or d.get("source_grades")!=EXPECTED
        or d.get("human_attestation_count")!=0
        or d.get("model_or_original_seals_modified") is not False
        or d.get("daily_repeat_source_calls_allowed") is not False):
        raise ArchiveRejected("ARCHIVE_HEADER_OR_PROVENANCE_CHANGED")
    rows=d.get("rows")
    if (not isinstance(rows,list) or len(rows)!=40
        or len(forecasts)!=40 or len(named)!=40):
        raise ArchiveRejected("ORIGINAL_COHORT_NOT_EXACTLY_40")
    previous=json.loads((root/"experiments/263/nov8_webreview_results_263.json").read_text(encoding="utf-8"))
    reviewed={(r["league"],r["home"],r["away"]):r for r in previous["rows"]}
    source_data=json.loads((root/"data/results_only_263/nov8_remaining36_source_review_20261112.json").read_text(encoding="utf-8"))
    src={(r["league"],r["home"],r["away"]):r for r in source_data["rows"]}
    if len(reviewed)!=40 or len(src)!=36:raise ArchiveRejected("PREVIOUS_SOURCE_REVIEW_CHANGED")
    got_sha=set();got_key=set();grades=defaultdict(int)
    for r in rows:
        sha=r.get("forecast_sha256");key=(r.get("league"),r.get("home"),r.get("away"))
        if (sha not in forecasts or sha not in named or sha in got_sha
            or key in got_key or key not in reviewed):
            raise ArchiveRejected("SHA_OR_MATCH_IDENTITY_INVALID")
        got_sha.add(sha);got_key.add(key)
        n=named[sha];f=forecasts[sha]["fixture"];old=reviewed[key]
        if (n.get("league")!=r["league"] or n.get("home")!=r["home"]
            or n.get("away")!=r["away"] or n.get("kickoff_utc")!=r["kickoff_utc"]
            or n.get("forecast_path")!=r["forecast_path"]
            or f["league"]!=r["league"] or f["kickoff_utc"]!=r["kickoff_utc"]
            or f["match_local_date"]!="2026-11-08"
            or f["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
            or r.get("match_date")!="2026-11-08"
            or r.get("human_attestation") is not False or
            r.get("daily_requery") is not False):
            raise ArchiveRejected("ORIGINAL_SHA_FIXTURE_OR_DAILY_LOCK_MISMATCH")
        kind=r.get("evidence_grade")
        if kind not in EXPECTED:raise ArchiveRejected("UNKNOWN_EVIDENCE_GRADE")
        grades[kind]+=1
        if old["status"]=="POSTPONED":
            if (r.get("match_state")!="POSTPONED_NO_SCORE"
                or r.get("score") is not None
                or kind!="POSTPONED_UNSCORED"
                or r.get("evidence_url")!=old["source_url"]
                or r.get("official_network_verified") is not False):
                raise ArchiveRejected("FABRICATED_POSTPONED_RESULT")
            continue
        if (r.get("match_state")!="FINISHED_ARCHIVED"
            or r.get("score")!=[old["home_goals"],old["away_goals"]]):
            raise ArchiveRejected("ARCHIVED_SCORE_CONFLICT")
        if kind=="TFF_NETWORK_VERIFIED":
            if (r["league"]!="TUR1" or r["home"] not in TFF
                or r["evidence_url"]!="https://www.tff.org/Default.aspx?macId="+TFF[r["home"]]+"&pageId=29"
                or r["official_network_verified"] is not True):
                raise ArchiveRejected("FAKE_DIRECT_TFF_PROOF")
        else:
            e=src.get(key)
            expected=("EXTERNAL_FEDERATION_WEB_RESEARCH" if e and e["source_class"]=="EXTERNAL_FEDERATION"
                      else "OFFICIAL_CLUB_WEB_RESEARCH" if e and e["source_class"]=="CLUB"
                      else "OFFICIAL_LEAGUE_WEB_RESEARCH" if e and e["source_class"]=="LEAGUE"
                      else None)
            if (kind!=expected or r["evidence_url"]!=e["new_score_evidence_url"]
                or r["official_network_verified"] is not False):
                raise ArchiveRejected("WEB_SOURCE_LEVEL_NOT_SAME_AS_PRIOR_RESEARCH")
    if got_sha!=set(forecasts) or got_key!=set(reviewed) or dict(grades)!=EXPECTED:
        raise ArchiveRejected("NOT_ALL_40_UNIQUELY_CLOSED")
    return d

def summary(d,forecasts,score_market,avg):
    scored=[];pending=[];groups=defaultdict(list);statuses=defaultdict(int)
    for r in d["rows"]:
        sha=r["forecast_sha256"]
        if r["score"] is None:
            pending.append({"forecast_sha256":sha,"league":r["league"],
                "home":r["home"],"away":r["away"],"status":"POSTPONED_ARCHIVED_NO_SCORE"})
            statuses["POSTPONED_ARCHIVED_NO_SCORE"]+=1
            continue
        label="ARCHIVED_"+r["evidence_grade"]
        for model,markets in score_market(forecasts[sha],r["score"]).items():
            groups[("ALL_PROVISIONAL",model)].append(markets)
            groups[(label,model)].append(markets)
        scored.append({"forecast_sha256":sha,"league":r["league"],
            "home":r["home"],"away":r["away"],"day":r["match_date"],
            "score":r["score"],"status":label,"source_url":r["evidence_url"],
            "archive_closed_no_daily_fetch":True})
        statuses[label]+=1
    def aggregate(part):
        return {"n":len(part),**{k:avg([p[k] for p in part])
            for k in ("MS","KG","OVER_1.5","OVER_2.5","OVER_3.5")}}
    classes=("ALL_PROVISIONAL",*("ARCHIVED_"+x for x in EXPECTED if x!="POSTPONED_UNSCORED"))
    return {"schema":"263_POSTMATCH_CSV_SOURCE_CANDIDATE_V1",
        "cohort":"new100","archive_closed":True,"daily_external_csv_calls":0,
        "registered":40,"provisional_scored":len(scored),"pending":len(pending),
        "human_attestations_written":0,"independent_federation_verified":3,
        "per_model":{c:{m:aggregate(groups[(c,m)]) for m in ("B","C2","C3","M4")}
                     for c in classes},
        "sources":{"archive":"STORED_NO_REPEAT_CSV_OR_TFF_REQUEST"},
        "status_counts":dict(statuses),"rows":scored,"pending_rows":pending,
        "forecast_modified":False,"models_retrained":False,"odds_api_calls":0,
        "limitations":["39 archived source-reviewed scores are NOT 39 live official-provider attestations",
          "3 source-pinned direct TFF reads; 35 official-site web research; 1 external-federation research",
          "1 postponed, unscored; 0 human-attested results; no model or odds changes",
          "Original 8 Nov records are terminal for daily scoring; no repeat source network lookup"]}

