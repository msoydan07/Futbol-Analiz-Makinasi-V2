"""Existing 2.6.3 read-only official fixture gate -> XGBoost research input.

Does not decide fixture truth by URLs or team text. Calls the existing
on-demand official-site lookup (actual fetch + canonical-ID validation);
a non-VERIFIED gate result fails closed. Research history uses the same
immutable 2.6.3 club IDs, eliminating unsafe OpenFootball name guesses.
No result, odds or 2.6.3 model outputs are created here.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from prospective_seal import dt,KNOWN_LEAGUES

SCHEMA="MC_VERIFIED_FIXTURE_INPUT_V1"
class GateBlocked(ValueError):pass

def convert_observation(observed,league,history_audit,*,now):
    now=dt(now.isoformat())
    if league not in KNOWN_LEAGUES or observed.get("status")!="VERIFIED":
        raise GateBlocked("OFFICIAL_FIXTURE_NOT_VERIFIED")
    if observed.get("league")!=league:
        raise GateBlocked("LEAGUE_MISMATCH")
    fields=("home_id","away_id","kickoff_utc","source_url","retrieved_at_utc")
    if any(not isinstance(observed.get(k),str) or not observed[k] for k in fields):
        raise GateBlocked("SOURCE_FIELDS_MISSING")
    h=observed["home_id"];a=observed["away_id"]
    if h==a or len(h)>96 or len(a)>96:
        raise GateBlocked("INVALID_IDENTITIES")
    kickoff=dt(observed["kickoff_utc"]);checked=dt(observed["retrieved_at_utc"])
    if not checked<=now<kickoff or now-checked>timedelta(minutes=15):
        raise GateBlocked("OFFICIAL_GATE_STALE_OR_KICKOFF_PASSED")
    if not (observed["source_url"].startswith("https://") and
        len(observed["source_url"])<=500):
        raise GateBlocked("BAD_OFFICIAL_URL")
    if history_audit.get("schema")!="MC_263_RESEARCH_SNAPSHOT_BRIDGE_V1" or not history_audit.get("accepted_for_limited_research"):
        raise GateBlocked("RESEARCH_HISTORY_NOT_ACCEPTED")
    # Reviewed snapshot time: do not claim more recent data than was accepted.
    history_asof=dt(history_audit["accepted_at_utc"])
    if history_asof>checked:
        raise GateBlocked("HISTORY_SNAPSHOT_NEWER_THAN_OFFICIAL_CHECK")
    fixture_id="fx-"+hashlib.sha256(
        json.dumps([league,h,a,kickoff.isoformat()],
                   separators=(",",":"),ensure_ascii=False).encode()).hexdigest()[:28]
    return {"schema":SCHEMA,"fixture_id":fixture_id,
      "league":league,"home_name":h,"away_name":a,
      "home_id":h,"away_id":a,"kickoff_utc":kickoff.isoformat(),
      "official_fixture_url":observed["source_url"],
      "source_verified_at_utc":checked.isoformat(),
      "history_asof_utc":history_asof.isoformat(),
      "fixture_verified_by":"EXTERNAL_OFFICIAL_GATE"}

def verified_manifest(league,home,away,history_audit,*,now=None,gate=None):
    now=now or datetime.now(timezone.utc)
    if gate is None:
        from analyze_named_match_gate import run as gate
    # Named-match gate fetches real official page and validates static IDs.
    observed=gate(league,home,away)
    return convert_observation(observed,league,history_audit,now=now)

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--league",required=True)
    p.add_argument("--home",required=True)
    p.add_argument("--away",required=True)
    p.add_argument("--history-audit",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    report=json.loads(Path(args.history_audit).read_text(encoding="utf8"))
    data=verified_manifest(args.league,args.home,args.away,report)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf8") as f:
        f.write(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"OFFICIAL_263_GATE_PASSED_RESEARCH_FIXTURE",
                      "league":data["league"],"fixture_id":data["fixture_id"],
                      "kickoff_utc":data["kickoff_utc"]},ensure_ascii=False))
if __name__=="__main__":main()
