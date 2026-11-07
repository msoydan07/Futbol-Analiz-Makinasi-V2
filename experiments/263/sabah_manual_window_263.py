"""Manual match-day analysis window, Turkey local time.

Chat command is the only intended trigger for the new100 workflow; this
function authorizes execution hours, not an automated run or API request.
Technical end-of-hour grace includes 14:00-14:59 for GitHub job start/finish.
Game kickoff and immutable forecast rules are checked separately.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TR=ZoneInfo("Europe/Istanbul")
START_HOUR=5
END_HOUR_EXCLUSIVE=15
DISPLAY_WINDOW="05:00–14:59 TSİ"

def in_manual_window(now:datetime)->bool:
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("AWARE_TIME_REQUIRED")
    local=now.astimezone(TR)
    return START_HOUR<=local.hour<END_HOUR_EXCLUSIVE
