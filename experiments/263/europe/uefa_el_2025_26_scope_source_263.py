"""2025/26 Europa League MISSING COHORT source acceptance, no model fitting.

The public fixture provider exposes 2025/26 Europa League scores as JSON.
This is an auxiliary source, not UEFA.com. Cross-check fixed named matches
against official UEFA's published 29 Jan 2026 results-by-team article.
ONLY games with BOTH clubs exact canonical-name aliases and both in the
2025/26 ten-league membership are returned for possible future model study.
Unknown / out-of-ten opponents are excluded, never investigated.

Fails CLOSED on missing/changed public feed, malformed scores, date, season,
incomplete league phase (36 clubs, 8 per club, 144 matches), conflicting
official anchor samples. Historical registry membership is still a claim,
not independent UEFA club-identity verification. No model or pilot changes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen

from uefa_ten_league_scope_gate_263 import norm,validated_index,LEAGUES

VERSION="263_EL_2025_26_TEN_LEAGUES_HISTORY_COHORT_COVERAGE_V1"
FEED_URL="https://fixturedownload.com/feed/json/europa-league-2025"
UEFA_OFFICIAL_REFERENCE="https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/"
SEASON="2025-2026"
EXPECTED_MATCHES=144
EXPECTED_GOALS=386
SOURCE_MAX_BYTES=210_000
# Independent name/date/score spot-check from UEFA published 29 January 2026.
UEFA_REFERENCE_ANCHORS=(
 ("2025-09-25","Aston Villa","Bologna",1,0),
 ("2025-10-02","Fenerbahçe","Nice",2,1),
 ("2025-10-23","Fenerbahçe","Stuttgart",1,0),
 ("2025-11-06","Aston Villa","M. Tel-Aviv",2,0),
 ("2026-01-22","Fenerbahçe","Aston Villa",0,1),
 ("2026-01-29","FCSB","Fenerbahçe",1,1),
)
DATES={1:{"2025-09-24","2025-09-25"},2:{"2025-10-02"},3:{"2025-10-23"},
       4:{"2025-11-06"},5:{"2025-11-27"},6:{"2025-12-11"},
       7:{"2026-01-22"},8:{"2026-01-29"}}

class CohortError(ValueError):pass

# Source-specific alias is proven by BOTH UEFA club history and Portugal league federation.
# Never update canonical registry and never guess any other club name.
OFFICIAL_ALIAS_BRIDGES={
    "braga":{"canonical_alias":"sc braga",
             "uefa_club_id":"52336",
             "uefa_club_history":"https://www.uefa.com/uefaeuropaleague/history/clubs/52336--braga/",
             "league_2025_26":"https://www.ligaportugal.pt/team/285/sc-braga/20252026"},
}

def referenced_alias(name,index):
    direct=index["aliases"].get(norm(name))
    if direct is not None:return direct,False
    bridge=OFFICIAL_ALIAS_BRIDGES.get(norm(name))
    if bridge is None:return None,False
    team_id=index["aliases"].get(bridge["canonical_alias"])
    if team_id is None:raise CohortError("PROVEN_ALIAS_NOT_IN_CANONICAL_INDEX")
    return team_id,True

def fetch_public_feed():
    req=Request(FEED_URL,headers={"User-Agent":"2.6.3-europe-source-audit/1.0",
                                  "Accept":"application/json"})
    with urlopen(req,timeout=15) as resp:
        final=resp.geturl()
        host=urlsplit(final).hostname
        if urlsplit(final).scheme!="https" or host not in {"fixturedownload.com","www.fixturedownload.com"}:
            raise CohortError("PUBLIC_FEED_REDIRECT_NOT_ALLOWED")
        data=resp.read(SOURCE_MAX_BYTES+1)
        content_type=resp.headers.get("Content-Type","").lower()
    if not data or len(data)>SOURCE_MAX_BYTES or "json" not in content_type:
        raise CohortError("PUBLIC_FEED_SIZE_OR_CONTENT_TYPE_REJECTED")
    return data

def decode_feed(data):
    if not isinstance(data,bytes) or not data:
        raise CohortError("FEED_MUST_BE_BYTES")
    try:raw=json.loads(data.decode("utf-8-sig"))
    except (UnicodeError,ValueError) as exc:raise CohortError("PUBLIC_FEED_INVALID_JSON") from exc
    if not isinstance(raw,list) or not 144<=len(raw)<=350:
        raise CohortError("FEED_RECORD_COUNT_INVALID")
    required={"MatchNumber","RoundNumber","DateUtc","HomeTeam","AwayTeam","HomeTeamScore","AwayTeamScore"}
    games=[];keys=set()
    for r in raw:
        if not isinstance(r,dict) or not required<=set(r):
            raise CohortError("PUBLIC_FEED_FIELDS_MISSING")
        md=r["RoundNumber"]
        if type(md) is not int:raise CohortError("ROUND_NUMBER_TYPE_INVALID")
        if not 1<=md<=8:continue  # only league phase; knockout excluded
        if not isinstance(r["DateUtc"],str) or not re.fullmatch(r"20\d\d-\d\d-\d\d \d\d:\d\d:\d\dZ",r["DateUtc"]):
            raise CohortError("LEAGUE_PHASE_UTC_DATE_INVALID")
        try:when=datetime.strptime(r["DateUtc"],"%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError as exc:raise CohortError("IMPOSSIBLE_DATE") from exc
        day=when.date().isoformat()
        if day not in DATES[md]:raise CohortError("LEAGUE_PHASE_UNEXPECTED_CALENDAR_DAY")
        home=r["HomeTeam"];away=r["AwayTeam"]
        if not isinstance(home,str) or not isinstance(away,str) or not home.strip() or not away.strip() or norm(home)==norm(away):
            raise CohortError("BAD_PARTICIPANT_NAMES")
        hg=r["HomeTeamScore"];ag=r["AwayTeamScore"]
        if type(hg) is not int or type(ag) is not int or not 0<=hg<=40 or not 0<=ag<=40:
            raise CohortError("UNPLAYED_OR_INVALID_GOALS")
        mid=r["MatchNumber"]
        if type(mid) is not int or mid<1:raise CohortError("INVALID_PROVIDER_MATCH_ID")
        key=(day,norm(home),norm(away))
        if key in keys:raise CohortError("DUPLICATE_LEAGUE_MATCH")
        keys.add(key)
        games.append({"match_provider_id":mid,"competition":"UEFA_EL","season":SEASON,
                      "matchday":md,"date":day,"kickoff_utc":when.isoformat(),
                      "home":home,"away":away,"home_goals":hg,"away_goals":ag})
    if len(games)!=EXPECTED_MATCHES:raise CohortError("UEFA_EL_2025_26_LEAGUE_PHASE_NOT_144")
    rounds=Counter(x["matchday"] for x in games)
    if rounds!={i:18 for i in range(1,9)}:raise CohortError("MATCHDAY_18_EACH_REQUIRED")
    teams=Counter()
    for r in games:teams.update((norm(r["home"]),norm(r["away"])))
    if len(teams)!=36 or set(teams.values())!={8}:
        raise CohortError("UEFA_EL_36_TEAMS_EIGHT_GAMES_REQUIRED")
    goals=sum(x["home_goals"]+x["away_goals"] for x in games)
    if goals!=EXPECTED_GOALS:raise CohortError("EXPECTED_386_GOALS_CHECK_FAILED")
    for day,h,a,gh,ga in UEFA_REFERENCE_ANCHORS:
        matches=[r for r in games if r["date"]==day and
                 norm(r["home"])==norm(h) and norm(r["away"])==norm(a) and
                 r["home_goals"]==gh and r["away_goals"]==ga]
        if len(matches)!=1:
            raise CohortError("UEFA_OFFICIAL_MATCH_REFERENCE_SPOT_CHECK_FAILED")
    return sorted(games,key=lambda r:(r["date"],r["matchday"],r["match_provider_id"]))

def audit_ten_league_scope(games,index,source_sha256):
    validated_index(index)
    if not isinstance(source_sha256,str) or not re.fullmatch(r"[a-f0-9]{64}",source_sha256):
        raise CohortError("FEED_SHA256_REQUIRED")
    members={id for league,ids in index["season_memberships"][SEASON].items() for id in ids}
    approved=[];excluded=Counter();unmatched=Counter();explicit_bridge_match_count=0
    for r in games:
        names=(r["home"],r["away"])
        links=tuple(referenced_alias(n,index) for n in names)
        ids=tuple(pair[0] for pair in links)
        if None in ids:
            excluded["UNKNOWN_NAME_NO_RESEARCH"]+=1
            for name,id in zip(names,ids):
                if id is None:unmatched[name]+=1
            continue
        if ids[0] not in members or ids[1] not in members:
            excluded["ONE_OR_BOTH_NOT_2025_26_TEN_LEAGUE_MEMBERS"]+=1
            continue
        if ids[0]==ids[1]:
            raise CohortError("CANONICAL_ID_COLLISION")
        explicit_bridge_match_count+=int(any(pair[1] for pair in links))
        approved.append({**r,"home_canonical_id_candidate":ids[0],
                         "away_canonical_id_candidate":ids[1],
                         "official_uefa_team_id_crosswalk_verified":False,
                         "source_verified_special_alias_used":any(pair[1] for pair in links),
                         "model_eligible":False})
    report={"version":VERSION,
        "source":{"feed_url":FEED_URL,"sha256":source_sha256,
                  "provider_not_UEFA_official":True,
                  "official_uefa_sample_reference":UEFA_OFFICIAL_REFERENCE,
                  "official_anchor_matches_checked":len(UEFA_REFERENCE_ANCHORS),
                  "all_144_matches_independently_uefa_verified":False},
        "coverage":{"league_phase_total":len(games),"league_phase_goals":EXPECTED_GOALS,
                    "teams":36,"2025_26_both_in_ten_leagues_name_candidates":len(approved),
                    "excluded_count":len(games)-len(approved),
                    "matches_with_source_verified_Braga_name_bridge":explicit_bridge_match_count,
                    "excluded_reasons":dict(excluded),
                    "unknown_names_for_manual_alias_review_only":dict(sorted(unmatched.items())),
                    "approved_for_cross_league_model":0},
        "data_provenance":"PUBLIC_FEED_PLUS_SIX_UEFA_SPOT_CHECKS_SOURCE_NOT_FULLY_VERIFIED",
        "identity_provenance":"EXACT_ALIAS_AND_2025_26_MEMBERSHIP_ONLY_NOT_UEFA_TEAM_ID_VERIFIED",
        "model_train_permitted":False,"mathematical_strength_bridge_computed":False,
        "h2h_experiment":False,"main_or_ten_league_data_modified":False,
        "pilot_recorded":False}
    if len(approved)+sum(excluded.values())!=len(games):
        raise CohortError("COVERAGE_PARTITION_MISMATCH")
    return report,approved

def main(argv=None):
    p=argparse.ArgumentParser(description="EL 2025/26 missing cohort audited from public data; NO model")
    p.add_argument("--identity-index",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--output",default="data/europe_staged_263/el_2025_26_ten_league_review")
    args=p.parse_args(argv)
    index=json.loads(Path(args.identity_index).read_text(encoding="utf-8"))
    payload=fetch_public_feed()
    games=decode_feed(payload)
    report,subset=audit_ten_league_scope(games,index,hashlib.sha256(payload).hexdigest())
    target=Path(args.output)
    if Path("data/europe_staged_263") not in target.parents:
        raise CohortError("OUTPUT_MUST_BE_QUARANTINED_EUROPE_STAGED")
    target.mkdir(parents=True,exist_ok=True)
    (target/"el_2025_26_source_acceptance.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (target/"el_2025_26_review_only_ten_leagues.json").write_text(
        json.dumps({"schema":VERSION,"matches":subset,"training_prohibited":True},
                   ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("EL_2025_26_ACCEPTANCE="+json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
