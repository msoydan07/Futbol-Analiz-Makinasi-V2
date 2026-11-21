"""EFL official 18-Nov 2026 Referee Appointments: 21-Nov Championship only.

The EFL article SSR HTML embeds its CMS richtext within a JS script, NOT
visible DOM nodes. We parse exact <h3>/<h4>/<h5> tags inside that original
on-demand official HTML. No bookmakers, odds, results, or cached fixtures.
"""
from datetime import datetime, timezone
from html import unescape
from zoneinfo import ZoneInfo
import re

PARSER="efl_referee_j16_20261121"
SOURCE="https://www.efl.com/news/2026/november/18/referee-appointments--20---26-november/"

def parse_efl_referee_j16(html):
    if (not isinstance(html,str) or len(html)>2_000_000
        or "Referee Appointments: 20 - 26 November" not in html
        or "18 Nov 2026" not in html):
        return []
    a=html.find("<h3>Sky Bet Championship</h3>")
    if a<0:return []
    b=html.find("<h3>Sky Bet League One</h3>",a)
    if b<0:return []
    section=html[a:b]
    start=section.find("<h4>Saturday 21 November</h4>")
    end=section.find("<h4>Sunday 22 November</h4>",start)
    if start<0 or end<=start:return []
    saturday=section[start:end]
    matches=re.findall(
        r"<h5>([^<>]+?)\s+v\s+([^<>]+?)\s+\((\d{1,2}):(\d{2})(am|pm)\)</h5>",
        saturday,flags=re.I)
    result=[]
    keys=set()
    for raw_home,raw_away,h,minute,ampm in matches:
        home=unescape(raw_home).strip();away=unescape(raw_away).strip()
        hour=int(h)%12+(12 if ampm.lower()=="pm" else 0)
        if hour>23 or int(minute)>59 or not home or not away or home==away:
            continue
        local=datetime(2026,11,21,hour,int(minute),tzinfo=ZoneInfo("Europe/London"))
        utc=local.astimezone(timezone.utc).isoformat()
        key=(home,away)
        if key in keys:raise ValueError("EFL_REFEREE_DUPLICATE_NAMED_MATCH")
        keys.add(key)
        result.append({"home":home,"away":away,"match_date":"2026-11-21",
                       "kickoff_utc":utc,"format":PARSER})
    # Exactly the user-date's 11 Championship fixtures must be present.
    # Incomplete article extraction fails closed instead of extrapolating.
    if len(result)!=11:return []
    if sum(1 for x in result if x["kickoff_utc"]=="2026-11-21T12:30:00+00:00")!=3:return []
    if sum(1 for x in result if x["kickoff_utc"]=="2026-11-21T15:00:00+00:00")!=8:return []
    return result
