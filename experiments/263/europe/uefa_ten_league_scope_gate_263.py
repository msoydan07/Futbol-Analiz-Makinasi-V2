"""PRE-RESEARCH UEFA named-match scope gate: the 10 domestic leagues, no others.

Run this before official fixture lookup, provider fetch, standings, odds, lineups,
cross-league ratings, or model math. No network, no UEFA scrape, no fuzzy match.
A named European match can proceed to *later separate verification* ONLY when
both supplied club names resolve unambiguously to current-season (2026/27)
memberships among the already curated ten domestic leagues.

This is a scope permit, NOT official UEFA identity or fixture verification.
Unrecognized names are blocked, not falsely claimed to be outside the ten.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

VERSION="263_UEFA_TEN_LEAGUE_PRE_RESEARCH_GATE_V1"
SEASON="2026-2027"
LEAGUES=frozenset(("ENG1","ENG2","GER1","ESP1","ITA1","FRA1",
                    "NED1","TUR1","POR1","BEL1"))
INDEX_TYPE="CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1"
INDEX_DEFAULT="experiments/263/evidence/identity_index_263.json"

class ScopeGateError(ValueError):
    pass

def norm(s):
    if not isinstance(s,str) or not s.strip() or len(s)>160:
        raise ScopeGateError("CLUB_NAME_REQUIRED")
    s=unicodedata.normalize("NFKC",s).casefold()
    s="".join(ch for ch in unicodedata.normalize("NFKD",s)
              if not unicodedata.combining(ch))
    return re.sub(r"\s+"," ",s).strip()

def validated_index(index):
    if not isinstance(index,dict) or index.get("index_type")!=INDEX_TYPE:
        raise ScopeGateError("CANONICAL_SOURCE_INDEX_INVALID")
    teams=index.get("teams")
    aliases=index.get("aliases")
    seasons=index.get("season_memberships")
    if not isinstance(teams,dict) or not isinstance(aliases,dict) or not isinstance(seasons,dict):
        raise ScopeGateError("CANONICAL_INDEX_FIELDS_MISSING")
    if set(seasons)!={"2025-2026",SEASON}:
        raise ScopeGateError("TEN_LEAGUE_SEASON_SCOPE_CHANGED")
    if any(set(leagues)!=LEAGUES for leagues in seasons.values()):
        raise ScopeGateError("TEN_LEAGUE_UNIVERSE_CHANGED")
    if not all(isinstance(clubs,list) and len(clubs)==len(set(clubs))
               and set(clubs)<=set(teams)
               for per_season in seasons.values() for clubs in per_season.values()):
        raise ScopeGateError("MEMBERSHIP_ID_INTEGRITY_FAILED")
    if any(club not in teams for club in aliases.values()):
        raise ScopeGateError("ALIAS_ID_INTEGRITY_FAILED")
    if any(norm(k)!=k for k in aliases):
        raise ScopeGateError("ALIAS_NORMALIZATION_MISMATCH")
    return index

def club_scope(name,index):
    key=norm(name)
    club_id=index["aliases"].get(key)
    if club_id is None:
        return {"supplied_name":name,"state":"IDENTITY_NOT_IN_REVIEWED_INDEX",
                "current_ten_league_membership":[],"safe_for_research":False,
                "canonical_team_id":None}
    leagues=[league for league,ids in index["season_memberships"][SEASON].items()
             if club_id in ids]
    if len(leagues)>1:
        raise ScopeGateError("TEAM_LISTED_IN_MULTIPLE_TEN_LEAGUES")
    if not leagues:
        return {"supplied_name":name,"state":"NOT_IN_CURRENT_TEN_LEAGUES",
                "current_ten_league_membership":[],
                "safe_for_research":False,"canonical_team_id":club_id}
    return {"supplied_name":name,"state":"IN_CURRENT_TEN_LEAGUES",
            "current_ten_league_membership":leagues,
            "safe_for_research":True,"canonical_team_id":club_id}

def check_europe_scope(home,away,index):
    validated_index(index)
    if norm(home)==norm(away):
        raise ScopeGateError("SAME_TEAM_REQUESTED")
    h=club_scope(home,index)
    a=club_scope(away,index)
    if h["canonical_team_id"] is not None and h["canonical_team_id"]==a["canonical_team_id"]:
        raise ScopeGateError("SAME_CANONICAL_TEAM_REQUESTED")
    in_scope=h["safe_for_research"] and a["safe_for_research"]
    states={h["state"],a["state"]}
    if in_scope:
        status="TEN_LEAGUES_SCOPE_PASSED_NOT_YET_VERIFIED"
        message="İki takım da 10 lig kapsamında. Resmî UEFA fikstürü ve diğer doğrulamalar henüz yapılmadı."
    elif "NOT_IN_CURRENT_TEN_LEAGUES" in states:
        status="ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES"
        message="Bu maçta kapsam dışı takım olduğu için analiz yapılmıyor."
    else:
        status="ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED"
        message="Bu maçta en az bir takımın 10 lig kapsamındaki kimliği doğrulanamadığı için analiz yapılmıyor."
    return {"version":VERSION,"season":SEASON,
            "status":status,"message":message,
            "home":h,"away":a,
            "allow_further_research":bool(in_scope),
            "official_match_verified":False,
            "uefa_team_identity_verified":False,
            "model_forecast_authorized":False,
            "odds_retrieved":False,
            "ABC_approved":False,
            "pilot_recorded":False,
            "main_or_domestic_10_leagues_modified":False}

def preflight_then(home,away,index,downstream):
    """Enforce a *call boundary*: never invoke expensive match research on STOP."""
    result=check_europe_scope(home,away,index)
    if not result["allow_further_research"]:
        return result,None
    if not callable(downstream):
        raise ScopeGateError("DOWNSTREAM_HANDLER_REQUIRED")
    return result,downstream(result)

def main(argv=None):
    p=argparse.ArgumentParser(description="Zero-network preflight for named UEFA match")
    p.add_argument("--home",required=True)
    p.add_argument("--away",required=True)
    p.add_argument("--index",default=INDEX_DEFAULT)
    args=p.parse_args(argv)
    index_path=Path(args.index)
    index=json.loads(index_path.read_text(encoding="utf-8"))
    result=check_europe_scope(args.home,args.away,index)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    # A stop is a planned policy decision, not GitHub Actions CI failure.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
