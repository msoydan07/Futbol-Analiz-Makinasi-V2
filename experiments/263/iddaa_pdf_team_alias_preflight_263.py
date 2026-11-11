"""Preflight exact team-name bridge for user-supplied iddaa.com PDFs, 10 leagues.

No second bookmaker lookup. Use canonical 215-team signed registry and already-
observed external spellings as a read-only sidecar. Existing source spellings
were seen in Nov 8 2026 Pinnacle snapshots, NOT proven iddaa spellings; this
sidecar is a spelling aid, not fixture evidence or independent price feed.

Actual match confirmation remains one official league/club fixture check;
this matcher only prevents alias differences from triggering extra lookups.
Never fuzzy-match, reverse home/away, alter original UUIDs, invent prices,
or silently replace truncated PDF labels.
"""
from __future__ import annotations
import json,re,unicodedata
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
REGISTRY=ROOT/"experiments/263/evidence/identity_index_263.json"
SEASON="2026-2027"
TR=ZoneInfo("Europe/Istanbul")
LEAGUES=("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
# Spelling variants actually present in previously archived external market
# source snapshots (Pinnacle via The Odds API, Nov 8 2026). NOT iddaa quotes.
# Values are existing canonical club names, never new IDs or fuzzy guesses.
KNOWN_EXTERNAL_VARIANTS={
  "BEL1":{
    "Union Saint-Gilloise":"Royale Union Saint-Gilloise",
    "Sint Truiden":"STVV"},
  "ENG1":{"Brighton and Hove Albion":"Brighton & Hove Albion"},
  "ESP1":{"Celta Vigo":"Celta",
          "Atlético Madrid":"Atlético de Madrid"},
  "GER1":{"Bayer Leverkusen":"Bayer 04 Leverkusen",
          "SC Freiburg":"Sport-Club Freiburg"},
  "ITA1":{"AC Milan":"Milan","Atalanta BC":"Atalanta",
          "Inter Milan":"Inter"},
  "NED1":{"FC Twente Enschede":"FC Twente"},
  "POR1":{"Académico de Viseu":"Académico",
          "CS Maritimo":"Marítimo M.",
          "CF Estrela":"Estrela Amadora",
          "Braga":"SC Braga"},
  "TUR1":{"Çaykur Rizespor":"ÇAYKUR RİZESPOR A.Ş.",
          "Erzurum BB":"ERZURUMSPOR FK",
          "Çorum FK":"ARCA ÇORUM FK",
          "Besiktas JK":"BEŞİKTAŞ A.Ş.",
          "Genclerbirligi SK":"GENÇLERBİRLİĞİ"},
}
assert sum(len(x) for x in KNOWN_EXTERNAL_VARIANTS.values())==20
# KNVB federation's live display spelling, with 2026-27 canonical N.E.C.
# Nijmegen identity pinned by the signed registry. Separate from bookmaker
# observed spellings; never claim that the Iddaa PDF used this alias.
OFFICIAL_SOURCE_VARIANTS={"NED1":{"N.E.C.":"N.E.C. Nijmegen"}}

def normal(s):
    if not isinstance(s,str):return ""
    s=s.strip().replace("ı","i").replace("İ","I").casefold()
    s="".join(c for c in unicodedata.normalize("NFKD",s)
              if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",s)

def is_truncated(value):
    return isinstance(value,str) and ("…" in value or "..." in value)

def index_registry(registry_path=REGISTRY):
    from mackolik_identity_gate_263 import _validate_identity_source,_memberships
    registry=json.loads(Path(registry_path).read_text(encoding="utf-8"))
    _validate_identity_source(registry)
    assert registry.get("index_type")=="CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1"
    members=_memberships(registry,SEASON)
    assert all(len(members.get(league,()))>0 for league in LEAGUES)
    byleague={}
    names={tid:t["name"] for tid,t in registry["teams"].items()}
    # Existing canonical aliases are already SHA-protected.
    known_per_id={}
    for a,tid in registry["aliases"].items():known_per_id.setdefault(tid,[]).append(a)
    for league in LEAGUES:
        aliases={}
        for tid in members[league]:
            labels=[registry["teams"][tid]["name"],registry["teams"][tid]["key"]]
            labels+=known_per_id.get(tid,[])
            for label in labels:
                token=normal(label)
                if not token:continue
                if token in aliases and aliases[token]!=tid:
                    raise ValueError("CANONICAL_TEAM_NAME_COLLISION_"+league+"_"+token)
                aliases[token]=tid
        # Add only curated mappings that point to an EXISTING team in the
        # requested league, and cannot collide with another canonical alias.
        for extra,canonical in KNOWN_EXTERNAL_VARIANTS.get(league,{}).items():
            canonical_token=normal(canonical)
            tid=aliases.get(canonical_token)
            if tid is None:raise ValueError("OVERRIDE_CANONICAL_TARGET_MISSING_"+league)
            new=normal(extra)
            if not new:raise ValueError("EMPTY_EXTERNAL_NAME")
            if new in aliases and aliases[new]!=tid:
                raise ValueError("EXTERNAL_TEAM_ALIAS_COLLISION_"+league)
            aliases[new]=tid
        for shown,canonical in OFFICIAL_SOURCE_VARIANTS.get(league,{}).items():
            tid=aliases.get(normal(canonical))
            if tid is None:raise ValueError("OFFICIAL_ALIAS_TARGET_MISSING_"+league)
            key=normal(shown)
            if key in aliases and aliases[key]!=tid:
                raise ValueError("OFFICIAL_ALIAS_COLLISION_"+league)
            aliases[key]=tid
        byleague[league]=aliases
    return byleague,names,members

def resolve_label(league,label,lookup=None):
    if lookup is None:lookup=index_registry()[0]
    if league not in lookup:
        return {"status":"NOT_IN_TEN_LEAGUES","label":label,"team_id":None}
    if is_truncated(label):
        return {"status":"TRUNCATED_PDF_TEAM_NAME","label":label,"team_id":None}
    token=normal(label)
    tid=lookup[league].get(token)
    if tid is None:
        return {"status":"UNMAPPED_NAME_SINGLE_MATCH_ONLY","label":label,
                "team_id":None}
    return {"status":"MAPPED","label":label,"team_id":tid}

def match_pdf_row(row,official_fixtures,index=None):
    """Only join to already ONE-TIME official fixture records.

    row {league,local_date,local_time,home,away} from PDF.
    official fixture {league,local_date,local_time,home_id,away_id}
    furnished by the EXISTING official league/club batch fixture gateway.
    No network or secondary name search. Blocking one row does not
    prevent unrelated rows being processed.
    """
    index=index if index is not None else index_registry()[0]
    league=row.get("league");home=row.get("home");away=row.get("away")
    h=resolve_label(league,home,index)
    a=resolve_label(league,away,index)
    if h["status"]!="MAPPED" or a["status"]!="MAPPED":
        return {"status":"SINGLE_ROW_NAME_REVIEW",
                "home_status":h["status"],"away_status":a["status"],
                "home_original":home,"away_original":away}
    if h["team_id"]==a["team_id"]:
        return {"status":"SINGLE_ROW_SAME_TEAM_INVALID"}
    # ISO day and time as visible on PDF. TZ-aware official source should
    # already be converted to Europe/Istanbul by the fixture gateway.
    candidates=[f for f in official_fixtures
                if f.get("league")==league and
                   f.get("local_date")==row.get("local_date") and
                   f.get("local_time")==row.get("local_time") and
                   f.get("home_id")==h["team_id"] and
                   f.get("away_id")==a["team_id"]]
    if len(candidates)!=1:
        return {"status":"SINGLE_ROW_OFFICIAL_FIXTURE_NOT_UNIQUE_OR_TIME_CHANGED",
                "matched_count":len(candidates),
                "home_id":h["team_id"],"away_id":a["team_id"]}
    f=candidates[0]
    return {"status":"MATCHED_TO_ONE_OFFICIAL_FIXTURE",
            "home_id":h["team_id"],"away_id":a["team_id"],
            "league":league,"local_date":row["local_date"],
            "local_time":row["local_time"],
            "source":"USER_IDDAA_PDF_PLUS_EXISTING_OFFICIAL_FIXTURE_BATCH",
            "odds_source_requires_second_bookmaker":False}

def preflight_batch(rows,fixtures,index=None):
    index=index if index is not None else index_registry()[0]
    results=[match_pdf_row(row,fixtures,index) for row in rows]
    return {"n_input":len(rows),"n_matched":sum(r["status"]=="MATCHED_TO_ONE_OFFICIAL_FIXTURE" for r in results),
            "n_single_row_review":sum(r["status"]!="MATCHED_TO_ONE_OFFICIAL_FIXTURE" for r in results),
            "records":results,
            "run_twice_for_unchanged_pdf":False,"price_api_calls":0,
            "modifies_existing_forecasts":False,
            "all_other_matched_rows_continue":True}
