"""Manual match intake for stage 5. User-provided data is NEVER official verification.
Usage: python manual_match_intake.py LEAGUE HOME AWAY YYYY-MM-DD HH:MM
Kickoff is interpreted as Europe/Istanbul local time. Outputs JSON; no bulk fixture.
"""
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LEAGUES = {"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"}

def intake(league, home, away, date, time):
    if league not in LEAGUES:
        return {"status":"REJECTED","reason":"unsupported_league"}
    home, away = home.strip(), away.strip()
    if not home or not away or home.casefold()==away.casefold():
        return {"status":"REJECTED","reason":"invalid_teams"}
    try:
        kickoff = datetime.strptime(date+" "+time,"%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Istanbul"))
    except ValueError:
        return {"status":"REJECTED","reason":"invalid_date_or_time"}
    if kickoff.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        return {"status":"REJECTED","reason":"kickoff_not_future"}
    return {
        "status":"MANUAL_INPUT_ACCEPTED",
        "league":league,"home":home,"away":away,
        "kickoff_local":kickoff.isoformat(),
        "kickoff_utc":kickoff.astimezone(timezone.utc).isoformat(),
        "fixture_verified":False,"source_type":"USER_SUPPLIED",
        "source_url":None,
        "analysis_gate":"PROVISIONAL_DATA_AUDIT_ONLY",
        "pilot_eligible":False,
        "first_xi_required":False,
        "warning":"Kullanici girdisi resmî fikstur dogrulamasi degildir. Tahmin pilotuna otomatik kabul edilmez."
    }

if __name__=="__main__":
    if len(sys.argv)!=6:
        raise SystemExit("Usage: python manual_match_intake.py LEAGUE HOME AWAY YYYY-MM-DD HH:MM")
    result=intake(*sys.argv[1:])
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result["status"]=="MANUAL_INPUT_ACCEPTED" else 1)
