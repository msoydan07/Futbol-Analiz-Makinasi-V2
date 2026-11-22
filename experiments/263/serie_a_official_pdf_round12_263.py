"""Read Italy's CURRENT official 2026-27 Serie A round-12 revised schedule.

ONE time-scoped, official *league-published* PDF: article "Anticipi e
posticipi fino alla fine del girone di andata" links to the official variation
document. The PDF prints all ten fixtures/dates/local kickoffs. A small,
strict word-alignment parser validates what the downloaded PDF says; there are
NO team/time literals used to generate observations.

Never infer a missing date/time, never fetch another host, never fall back to
iddaa odds as source. This source is applicable ONLY to 21–23 Nov 2026.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timezone
from urllib.request import Request, build_opener
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import hashlib
import re

PDF_URL="https://images.legaseriea.it/image/private/fl_attachment/prd/w2zepi8iww3zamzewn8y.pdf"
PARSER="seriea_official_revision_pdf_round12_2026"
MAX_BYTES=2_500_000
DATE_RE=re.compile(r"\b(2[123])/11/2026\b")
TIME_RE=re.compile(r"\b([0-2]?\d)[.:]([0-5]\d)\b")
PAIR_RE=re.compile(r"\b([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)\s*[-–]\s*([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)\b")


def parse_pdf_events(raw):
    if not isinstance(raw,bytes) or len(raw)<1000 or not raw.startswith(b"%PDF"):
        raise ValueError("NOT_A_COMPLETE_OFFICIAL_PDF")
    import fitz
    doc=fitz.open(stream=raw,filetype="pdf")
    if len(doc)!=1 or doc.is_encrypted:
        raise ValueError("OFFICIAL_ROUND12_PDF_PAGE_COUNT_OR_ENCRYPTION_INVALID")
    page=doc[0]
    words=page.get_text("words")
    header=" ".join(w[4] for w in words)
    if ("SERIE A ENILIVE" not in header.upper()
        or "2026/27" not in header
        or "12" not in header):
        raise ValueError("OFFICIAL_ITALY_ROUND12_HEADER_MISSING")
    # Group PDF glyphs by visual table-row baseline, not the PDF's text block
    # extraction order, which can be column-first rather than row-first.
    grouped=[]
    for word in sorted(words,key=lambda w:(w[1],w[0])):
        y=word[1]
        if grouped and abs(grouped[-1][0]-y)<2.8:
            grouped[-1][1].append(word)
        else:
            grouped.append([y,[word]])
    result=[]
    for _,w in grouped:
        line=" ".join(z[4] for z in sorted(w,key=lambda z:z[0]))
        dm=DATE_RE.search(line)
        if not dm:continue
        tm=TIME_RE.search(line[dm.end():])
        if not tm:continue
        hr,minute=map(int,tm.groups())
        if hr>23:continue
        # The final table column is the TV license holder. Never let
        # its words be absorbed into the away-team name (e.g. "Inter DAZN").
        # This exact official round-12 format always shows DAZN(/SKY).
        license_holder=re.search(r"\\s+DAZN(?:/SKY)?\\s*$",line,re.I)
        if license_holder is None:continue
        match_area=line[dm.end():license_holder.start()]
        pair=PAIR_RE.search(match_area)
        if not pair:continue
        home,away=(x.strip() for x in pair.groups())
        if home.casefold()==away.casefold():continue
        day=int(dm.group(1))
        dt=datetime(2026,11,day,hr,minute,tzinfo=ZoneInfo("Europe/Rome"))
        result.append({
            "home":home,"away":away,
            "match_date":dt.date().isoformat(),
            "kickoff_utc":dt.astimezone(timezone.utc).isoformat(),
            "format":PARSER,
        })
    unique={(x["home"],x["away"],x["match_date"]):x for x in result}
    # 12th round is exactly ten unique league games in this particular
    # published PDF; a truncated/changed document is NOT official evidence.
    if len(result)!=10 or len(unique)!=10:
        raise ValueError("OFFICIAL_SERIE_A_ROUND12_EXPECTED_TEN_UNIQUE_GAMES")
    return list(unique.values())


def fetch_and_parse():
    from official_page_lookup_263 import _OfficialRedirect, is_approved_url
    if not is_approved_url(PDF_URL,"ITA1"):
        raise ValueError("UNAPPROVED_SERIE_A_PDF_HOST")
    opener=build_opener(_OfficialRedirect("ITA1"))
    with opener.open(Request(PDF_URL,headers={
             "User-Agent":"Mozilla/5.0 (official fixture audit)",
             "Accept":"application/pdf"}),timeout=15) as res:
        effective=res.geturl()
        if not is_approved_url(effective,"ITA1"):
            raise ValueError("OFFICIAL_PDF_REDIRECT_UNTRUSTED")
        if "pdf" not in res.headers.get("Content-Type","").lower():
            raise ValueError("OFFICIAL_PDF_MIME_INVALID")
        raw=res.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("OFFICIAL_PDF_TOO_LARGE")
    events=parse_pdf_events(raw)
    return effective,events,hashlib.sha256(raw).hexdigest()
