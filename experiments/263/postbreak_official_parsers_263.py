"""Strict post-break fixture article readers for official, dated league pages.

No manual fixture injection and no inference from generic commentary. A parser
admits an event only when the named official date/time/team line is present,
the complete round is unambiguous, and the source-specific window matches.
No historical model, financial quote, or stored pilot data is touched.
"""
from __future__ import annotations
import html as html_lib
import re
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from official_page_lookup_263 import _Markup

def _lines(markup):
    return [" ".join(x.split()).strip() for x in "".join(markup.visible).splitlines()
            if x.strip()]

def parse_tff_round12(html):
    if not isinstance(html,str) or len(html)>2_000_000:return []
    p=_Markup();p.feed(html)
    visible=re.sub(r"\s+"," ","".join(p.visible))
    if ("Trendyol Süper Lig" not in visible
        or "2026-2027 Sezonu Fikstürü" not in visible
        or not re.search(r"\b12\s*\.\s*Hafta\b",visible,re.I)):
        return []
    out=[]
    for row in p.rows:
        if len(row)!=5 or row[2]!="-" or row[4].casefold()!="detaylar":continue
        match=re.fullmatch(r"(2[123]\.11\.2026)\s+((?:[01]?\d|2[0-3]):[0-5]\d)",row[0])
        if not match:continue
        home,away=row[1].strip(),row[3].strip()
        if not home or not away or home.casefold()==away.casefold():return []
        try:
            instant=datetime.strptime(match.group(1)+" "+match.group(2),"%d.%m.%Y %H:%M")
            instant=instant.replace(tzinfo=ZoneInfo("Europe/Istanbul"))
        except ValueError:return []
        out.append({"home":home,"away":away,"match_date":instant.date().isoformat(),
                    "kickoff_utc":instant.astimezone(timezone.utc).isoformat(),
                    "format":"tff_2026_week12"})
    if len(out)!=9 or len({(x["home"],x["away"],x["kickoff_utc"]) for x in out})!=9:
        return []
    return out

def parse_ligue1_round11(html):
    if not isinstance(html,str) or len(html)>2_000_000:return []
    p=_Markup();p.feed(html)
    lines=_lines(p)
    if not any("Programmations TV : J10 et J11" in s for s in lines):return []
    section=False;current=None;out=[]
    title=re.compile(r"^11e\s+JOURNÉE\s+DE\s+LIGUE\s+1",re.I)
    clock=re.compile(r"^(Vendredi|Samedi|Dimanche)\s+(20|21|22)\s+novembre\s+2026\s+à\s+(\d{1,2})h(\d{2})\s+sur\s+Ligue\s+1\+",re.I)
    weekdays={20:"vendredi",21:"samedi",22:"dimanche"}
    pair=re.compile(r"^(.{2,85}?)\s+[–-]\s+(.{2,85}?)$")
    for line in lines:
        if title.match(line):section=True;current=None;continue
        if not section:continue
        if line.startswith("→ Abonnez-vous") or re.match(r"^12e\s+JOURNÉE",line,re.I):break
        marker=clock.match(line)
        if marker:
            day=int(marker.group(2))
            current=(day,int(marker.group(3)),int(marker.group(4))) if marker.group(1).casefold()==weekdays[day] else None
            continue
        if current is None:continue
        match=pair.fullmatch(line)
        if not match:continue
        home,away=match.group(1).strip(),match.group(2).strip()
        if home==away or len(home)<2 or len(away)<2:return []
        try:at=datetime(2026,11,*current,tzinfo=ZoneInfo("Europe/Paris"))
        except ValueError:return []
        out.append({"home":home,"away":away,"match_date":at.date().isoformat(),
                    "kickoff_utc":at.astimezone(timezone.utc).isoformat(),
                    "format":"ligue1_2026_round11_tv"})
    counts={day:sum(e["match_date"]==f"2026-11-{day}" for e in out) for day in (20,21,22)}
    if counts!={20:1,21:5,22:3}:return []
    if len({(e["home"],e["away"],e["kickoff_utc"]) for e in out})!=9:return []
    return out

def parse_portugal_round12(html):
    if not isinstance(html,str) or not 100<=len(html)<=2_000_000:return []
    if "12.a-jornada" not in html and "12.ª jornada" not in html:return []
    # Official Nuxt embeds escaped <p> article paragraphs in JSON. Only decode
    # the fixed article text; do NOT search the other league's generic calendar.
    decoded=html.replace(r"\u003C","<").replace(r"\u003E",">").replace(r"\u0026","&")
    decoded=decoded.replace(r"\"","\"")
    decoded=decoded.replace(r"\n","\n")
    decoded=html_lib.unescape(decoded)
    p=_Markup();p.feed(decoded)
    lines=_lines(p)
    section=False;day=None;out=[]
    heading=re.compile(r"^(Sexta-feira|Sábado|Domingo|Segunda-feira),?\s+(27|28|29|30)\s+de\s+novembro$",re.I)
    days={27:"sexta-feira",28:"sábado",29:"domingo",30:"segunda-feira"}
    row=re.compile(r"^(.{2,90}?)\s+[-–]\s+(.{2,90}?),\s*(\d{1,2})h([0-5]\d)\s*[-–]\s*(?:SportTV|Sport TV|TVI|BTV)\b",re.I)
    for line in lines:
        if re.fullmatch(r"Jornada\s+12",line,re.I):section=True;continue
        if not section:continue
        if line.startswith("Consulte AQUI") or line.startswith("Consulte aqui"):break
        hm=heading.fullmatch(line)
        if hm:
            n=int(hm.group(2));day=n if hm.group(1).casefold()==days[n] else None
            continue
        m=row.match(line)
        if m is None or day is None:continue
        home,away,h,minute=(x.strip() for x in m.groups())
        if not home or not away or home.casefold()==away.casefold():return []
        try:at=datetime(2026,11,day,int(h),int(minute),tzinfo=ZoneInfo("Europe/Lisbon"))
        except ValueError:return []
        out.append({"home":home,"away":away,"match_date":at.date().isoformat(),
                    "kickoff_utc":at.astimezone(timezone.utc).isoformat(),
                    "format":"ligaportugal_2026_round12_tv"})
    counts={d:sum(e["match_date"]==f"2026-11-{d}" for e in out) for d in (27,28,29,30)}
    if counts!={27:1,28:4,29:2,30:2}:return []
    if len({(e["home"],e["away"],e["kickoff_utc"]) for e in out})!=9:return []
    return out
