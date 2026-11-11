"""User supplied iddaa.com print-to-PDF bulletin -> source-stamped PRE-analysis odds rows.

Read only. Does NOT scrape, query or independently re-verify bookmaker odds.
Extracts only MS 1/X/2, 2.5 Alt/Üst, KG Var/Yok. Never creates model picks.
PDF is not trusted as "current" after its embedded creation timestamp.
A league/cell that cannot be parsed is one-row REVIEW, not a silent guess.
The old 2.6.3 post-forecast 10-minute quote handler is intentionally NOT
used: source-PDF-first ordering has different temporal provenance.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TR=ZoneInfo("Europe/Istanbul")
SCHEMA="263_iddaa_pdf_pregame_bulletin_v1"
SOURCE="https://www.iddaa.com/program/futbol"
# These anticipated league headings are INITIAL lookup aids, not verified
# claims about iddaa UI nomenclature. Unrecognized labels remain review-only.
LABELS={
 "ENG1":("İNGİLTERE PREMIER LİG","İNGİLTERE PREMIER LİGİ",
         "İNGİLTERE PREMIER LEAGUE","İNGİLTERE PREMİER LİG",
         "İNGİLTERE PREMİER LİGİ","PREMIER LEAGUE, İNGİLTERE"),
 "ENG2":("İNGİLTERE CHAMPIONSHIP","İNGİLTERE CHAMPİONSHİP",
         "İNGİLTERE ŞAMPİYONLUK LİGİ","İNGİLTERE EFL CHAMPIONSHIP"),
 "GER1":("ALMANYA BUNDESLİGA","ALMANYA BUNDESLIGA",
         "ALMANYA 1.BUNDESLIGA","ALMANYA BUNDESLİGA 1"),
 "ESP1":("İSPANYA LA LİGA","İSPANYA LALIGA",
         "İSPANYA 1.LİG","İSPANYA PRIMERA DIVISION"),
 "ITA1":("İTALYA SERİE A","İTALYA SERIE A","İTALYA SERİ A",
         "İTALYA 1.LİG"),
 "FRA1":("FRANSA LİG 1","FRANSA LİGUE 1","FRANSA 1.LİG",
         "FRANSA 1.LİGİ"),
 "NED1":("HOLLANDA EREDIVISIE","HOLLANDA EREDİVİSİE",
         "HOLLANDA 1.LİG","HOLLANDA EREDIVISIE 1"),
 "TUR1":("TÜRKİYE SÜPER LİG","TÜRKİYE SÜPER LİGİ",
         "TÜRKİYE TRENDYOL SÜPER LİG","TÜRKİYE SÜPER LIG"),
 "POR1":("PORTEKİZ PRİMEİRA LİGA","PORTEKİZ PRIMEIRA LIGA",
         "PORTEKİZ 1.LİG","PORTEKİZ LİGA PORTUGAL"),
 "BEL1":("BELÇİKA PRO LEAGUE","BELÇİKA JUPILER PRO LEAGUE",
         "BELÇİKA 1.LİG","BELÇİKA JUPILER LİG"),
}
PRICE_NAMES=("MS1","MSX","MS2","IY1","IYX","IY2","HANDICAP",
             "HMS1","HMSX","HMS2","O25_UNDER","O25_OVER","BTTS_YES","BTTS_NO")
KEEP=("MS1","MSX","MS2","O25_UNDER","O25_OVER","BTTS_YES","BTTS_NO")
TOKEN=re.compile(r"^(?:\d+(?:\.\d+)?|\d+:\d+|-)$")
TIME=re.compile(r"^\d\d:\d\d$")
_CREATION=re.compile(r"^D:(\d{14})([Zz]|[+-]\d\d'?\d\d'?)?")
_SENTINEL=("KADIN","WOMEN","U19","U21","U17","YOUTH",
           "KUPASI","CUP","HAZIRLIK","AMATÖR","RESERVE","B TAKIM")

def normal(t):
    import unicodedata
    t=t.strip().replace("İ","I").replace("ı","i").casefold()
    t="".join(x for x in unicodedata.normalize("NFKD",t)
              if not unicodedata.combining(x))
    return re.sub(r"[^a-z0-9]","",t)

def league_lookup(label):
    n=normal(label)
    if not n:return None
    for word in _SENTINEL:
        if normal(word) in n:return None
    choices=[league for league,names in LABELS.items()
             if any(normal(name)==n for name in names)]
    return choices[0] if len(choices)==1 else None

def capture_time(meta,override=None):
    if override is not None:
        parsed=datetime.fromisoformat(override.replace("Z","+00:00"))
        if parsed.tzinfo is None:raise ValueError("PDF_OBSERVED_TIME_NEEDS_TIMEZONE")
        return parsed.astimezone(timezone.utc)
    source=meta.get("creationDate","")
    m=_CREATION.fullmatch(source)
    if not m:raise ValueError("PDF_CREATION_TIMESTAMP_UNAVAILABLE_SUPPLY_OBSERVED_UTC")
    value=datetime.strptime(m.group(1),"%Y%m%d%H%M%S")
    offset=m.group(2)
    if offset=="Z":offset="+00'00'"
    if not offset:raise ValueError("PDF_CREATION_TIMESTAMP_WITHOUT_TIMEZONE")
    digits=re.findall(r"\d\d",offset)
    if len(digits)<2:raise ValueError("PDF_CREATION_TIMESTAMP_BAD_OFFSET")
    tz=timezone(timedelta(hours=int(digits[0]),minutes=int(digits[1]))
                *(1 if offset[0]=="+" else -1))
    return value.replace(tzinfo=tz).astimezone(timezone.utc)

def _heading(page,b):
    """Find ONE printed day header and left-hand league name above row."""
    heads=[h for h in page.get_text("blocks")
           if h[1]<=b[1] and b[1]-h[1]<=30
           and re.search(r"(?:^|\n)(Bugün|Yarın)\n",h[4])]
    if not heads:return None,None
    h=max(heads,key=lambda x:x[1])
    day=re.search(r"(?:^|\n)(Bugün|Yarın)\n",h[4]).group(1)
    embedded=re.split(r"\b(?:Bugün|Yarın)\b",h[4],maxsplit=1)[0].strip()
    extra=[]
    for other in page.get_text("blocks"):
        if other[0]>=185 or other is h or other is b:continue
        if h[1]-10<=other[1]<=h[1]+10 and other[1]<b[1]-6:
            chunk=other[4].strip()
            if chunk and not re.search(r"\b(?:Bugün|Yarın)\b",chunk):
                extra.append((other[1],chunk))
    extra.sort()
    league=" ".join([t for _,t in extra]+([embedded] if embedded else []))
    return day,league.strip()

def _markets_from_words(page,b):
    # Printed CSS grid has 14 positions. Never shift columns when a dash is
    # missing: accepting 13 tokens would turn an unrelated HMS quote into 2.5.
    # The kickoff/team block is separate from price cells; x>=204 captures
    # the responsive print layout in the real 11 Nov sample.
    target_y=b[1]+3
    words=[(w[0],w[4]) for w in page.get_text("words")
           if abs(w[1]-target_y)<1.8 and 204<=w[0]<=445
           and TOKEN.fullmatch(w[4])
           and (w[4]=="-" or "." in w[4] or ":" in w[4])]
    words.sort(key=lambda item:item[0])
    raw=[text for _,text in words]
    if len(raw)!=14:
        return None,{"status":"PRICE_COLUMN_ALIGNMENT_UNRESOLVED",
                     "found_slots":len(raw),"visible_tokens":raw}
    if raw[6]!="-" and not re.fullmatch(r"\d+:\d+",raw[6]):
        return None,{"status":"HANDICAP_COLUMN_WRONG","visible_tokens":raw}
    if any(":" in token for i,token in enumerate(raw) if i!=6):
        return None,{"status":"BAD_PRICE_COLUMN_ORDER","visible_tokens":raw}
    result={}
    for key,val in zip(PRICE_NAMES,raw):
        if key not in KEEP:continue
        if val=="-":result[key]=None;continue
        try:
            number=float(val)
            if not 1<number<=1000:raise ValueError
            result[key]=number
        except (ValueError,TypeError):
            return None,{"status":"INVALID_QUOTE_VALUE","column":key,"value":val}
    return result,{"status":"PRICE_COLUMNS_READ","found_slots":14}

def parse_pdf(pdf_path,observed_at_utc=None):
    """Generate an auditable JSON payload, never a betting recommendation."""
    try:import fitz
    except ImportError as exc:raise RuntimeError("Install PyMuPDF for printed PDF extraction") from exc
    source=Path(pdf_path);raw=source.read_bytes()
    doc=fitz.open(stream=raw,filetype="pdf")
    meta=doc.metadata
    if "iddaa" not in (meta.get("title") or "").lower():
        raise ValueError("NOT_IDDAA_PRINT_TITLE")
    if not any("Bülten" in pg.get_text() for pg in doc):
        raise ValueError("IDDAA_BULLETIN_TEXT_MISSING")
    observed=capture_time(meta,observed_at_utc)
    local=observed.astimezone(TR)
    rows=[]
    for page_number,page in enumerate(doc,1):
        for b in page.get_text("blocks"):
            lines=b[4].splitlines()
            if len(lines)<2 or not TIME.fullmatch(lines[0]):continue
            if " - " not in lines[1] and not re.search(r"\s+-\S",lines[1]):continue
            parts=re.split(r"\s+-\s*",lines[1],maxsplit=1)
            if len(parts)!=2:continue
            home,away=(t.strip() for t in parts)
            if not home or not away:continue
            day,heading=_heading(page,b)
            if not day:continue
            fixture_date=(local.date()+timedelta(days=day=="Yarın")).isoformat()
            league=league_lookup(heading)
            odds,price_state=_markets_from_words(page,b)
            clipped=any(marker in home+away for marker in ("…","..."))
            state=("OUT_OF_SCOPE_OR_UNMAPPED_LEAGUE" if league is None else
                   "TRUNCATED_TEAM_NAME_SINGLE_ROW" if clipped else
                   price_state["status"] if odds is None else
                   "PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK")
            rows.append({"page":page_number,"league_label":heading,
                         "league":league,"match_date_tr":fixture_date,
                         "kickoff_time_tr":lines[0],"home_label":home,
                         "away_label":away,"odds":odds,
                         "price_parse":price_state,"status":state})
    report={"schema":SCHEMA,"source_url":SOURCE,"source_domain":"iddaa.com",
            "source_scope":"USER_SUPPLIED_PDF_NOT_NETWORK_REVERIFIED",
            "pdf_sha256":hashlib.sha256(raw).hexdigest(),
            "pdf_capture_utc":observed.isoformat(),"pdf_capture_tr":local.isoformat(),
            "pdf_title":meta.get("title"),"total_visible_fixtures":len(rows),
            "potential_ten_league_rows":sum(r["league"] is not None for r in rows),
            "source_odds_are_observed_not_current":True,
            "no_bookmaker_api_calls":True,
            "no_model_forecasts_created":True,"rows":rows}
    if not rows:raise ValueError("NO_READABLE_FIXTURE_ROWS")
    return report

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--pdf",required=True)
    a.add_argument("--out",required=True)
    a.add_argument("--observed-at-utc",default=None)
    args=a.parse_args()
    report=parse_pdf(args.pdf,args.observed_at_utc)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as file:
        json.dump(report,file,ensure_ascii=False,indent=2,sort_keys=True)
        file.write("\n")
    print(json.dumps({"out":str(out),"pdf_sha256":report["pdf_sha256"],
        "rows":len(report["rows"]),"candidate_league_rows":report["potential_ten_league_rows"]}))

if __name__=="__main__":main()
