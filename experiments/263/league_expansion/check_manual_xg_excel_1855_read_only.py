#!/usr/bin/env python3
"""Read-only QA for the user's established 1855-match xG Excel workbook.

Python stdlib only, no xlsx changes, no uploaded match-by-match data and
no M4 training. Workbook must preserve its five original sheets and columns.
"""
import argparse
import collections
import datetime
import json
import math
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

N="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SHEETS={"EKSIK_2026":(2,90),"EKSIK_2025":(3,1765),
        "ESKI_459_KONTROL":(4,459),"HAFTALIK_YENI":(5,None)}
NEEDED={"A":"Tarih","B":"Ev sahibi","C":"Deplasman","D":"Skor",
        "E":"EV xG YAZ","F":"DEP xG YAZ","G":"Kaynak maç URL",
        "H":"Baktığın tarih","J":"Lig"}
CODES={"ENG1","ENG2","GER1","ESP1","ITA1","FRA1",
       "NED1","TUR1","POR1","BEL1"}
DATE=datetime.date

def sheet_rows(zipf,number,strings):
    root=ET.fromstring(zipf.read("xl/worksheets/sheet%d.xml"%number))
    result=[]
    for node in root.findall(".//"+N+"sheetData/"+N+"row"):
        cells={}
        for c in node.findall(N+"c"):
            address=c.attrib.get("r","")
            m=re.match(r"^([A-Z]+)\d+$",address)
            if not m:continue
            raw=c.find(N+"v")
            value=raw.text if raw is not None else ""
            if c.attrib.get("t")=="s" and value:value=strings[int(value)]
            if c.attrib.get("t")=="inlineStr":
                value="".join(x.text or "" for x in c.iter(N+"t"))
            cells[m.group(1)]=(value or "",c.find(N+"f") is not None,c.attrib.get("t",""))
        result.append((int(node.attrib.get("r","1")),cells))
    return result

def value(row,col):
    return row.get(col,("",False,""))[0]

def valid_date(v):
    if re.fullmatch(r"20\d\d-\d\d-\d\d",v):
        return DATE.fromisoformat(v)
    raise ValueError("DATE_MUST_BE_ISO_TEXT")

def xg(cell):
    s,formula,kind=cell
    if formula:raise ValueError("USER_INPUT_IS_FORMULA")
    if s=="":return None
    if kind not in ("n",""):raise ValueError("XG_MUST_BE_NUMERIC_CELL")
    if not re.fullmatch(r"(?:\d{1,2})(?:\.\d{1,6})?",s):
        raise ValueError("XG_BAD_NUMBER")
    v=float(s)
    if not math.isfinite(v) or v<0 or v>15:raise ValueError("XG_OUT_OF_RANGE")
    return v

def audit(workbook):
    path=Path(workbook)
    if path.stat().st_size>6000000:raise ValueError("XLSX_TOO_LARGE")
    with zipfile.ZipFile(path) as z:
        entries=z.namelist()
        if any(x.startswith("xl/externalLinks/") or "vbaProject" in x for x in entries):
            raise ValueError("MACRO_OR_EXTERNAL_LINK_BLOCKED")
        if sum(i.file_size for i in z.infolist())>24000000:
            raise ValueError("ZIP_BOMB_GUARD")
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        names=[x.attrib["name"] for x in wb.findall(".//"+N+"sheets/"+N+"sheet")]
        if names!=["BASLA",*SHEETS]:raise ValueError("WORKBOOK_SHEET_NAMES_OR_ORDER_CHANGED")
        shared=ET.fromstring(z.read("xl/sharedStrings.xml"))
        strings=["".join(t.text or "" for t in si.iter(N+"t")) for si in shared.findall(N+"si")]
        count=collections.Counter()
        by_league=collections.Counter()
        problems=[]
        uuids=set();identities=set()
        for tab,(sheet_no,expected) in SHEETS.items():
            rows=sheet_rows(z,sheet_no,strings)
            if not rows:raise ValueError("MISSING_SHEET:"+tab)
            header=rows[0][1]
            for col,title in NEEDED.items():
                actual=value(header,col)
                if col=="A" and tab=="HAFTALIK_YENI":title="Maç tarihi"
                if actual!=title:raise ValueError("HEADER_CHANGED:"+tab+":"+col)
            data=[(r,cell) for r,cell in rows[1:] if any(value(cell,c) for c in ("A","B","C","D","E","F","G","H","J"))]
            if expected is not None and len(data)!=expected:
                raise ValueError("BASELINE_SHEET_ROW_COUNT_CHANGED:"+tab)
            count[tab+"_rows"]=len(data)
            for rowno,r in data:
                label=tab+":"+str(rowno)
                try:
                    day=valid_date(value(r,"A"))
                    home=value(r,"B").strip();away=value(r,"C").strip()
                    league=value(r,"J").strip()
                    score=value(r,"D").strip()
                    if not home or not away or home.casefold()==away.casefold():
                        raise ValueError("INVALID_TEAM_NAMES")
                    if league not in CODES:raise ValueError("UNKNOWN_LEAGUE")
                    if not re.fullmatch(r"\d{1,2}-\d{1,2}",score):
                        raise ValueError("INVALID_FINAL_SCORE")
                    season="2026-27" if tab=="EKSIK_2026" else "2025-26"
                    if tab=="HAFTALIK_YENI":season=value(r,"K")
                    if season not in ("2025-26","2026-27"):
                        raise ValueError("INVALID_SEASON")
                    if day>datetime.date.today():raise ValueError("FUTURE_MATCH")
                    if day<DATE(2025,7,1) if season=="2025-26" else day<DATE(2026,7,1):
                        raise ValueError("MATCH_OUTSIDE_SEASON")
                    k=(league,season,day.isoformat(),home.casefold(),away.casefold())
                    if k in identities:raise ValueError("DUPLICATE_MATCH")
                    identities.add(k)
                    if tab!="HAFTALIK_YENI":
                        idcol="P" if tab=="ESKI_459_KONTROL" else "M"
                        fid=value(r,idcol)
                        uuid.UUID(fid)
                        if fid in uuids:raise ValueError("DUPLICATE_FIXTURE_ID")
                        uuids.add(fid)
                    oldone=tab.startswith("EKSIK") and bool(value(r,"K"))!=bool(value(r,"L"))
                    count["old_vendor_one_sided_pairs"]+=int(oldone)
                    a=xg(r.get("E",("",False,"")))
                    b=xg(r.get("F",("",False,"")))
                    if a is None and b is None:
                        count["still_blank"]+=1
                        continue
                    if a is None or b is None:
                        count["partial_input_pairs"]+=1
                        raise ValueError("BOTH_NEW_SOURCE_XG_VALUES_REQUIRED")
                    count["new_xg_numeric_pairs"]+=1
                    u=value(r,"G").strip()
                    p=urlsplit(u)
                    if r.get("G",("",False,""))[1]:
                        raise ValueError("URL_CELL_FORMULA")
                    if p.scheme!="https" or p.hostname not in ("xg.football","www.xg.football") or p.path in ("","/"):
                        raise ValueError("DIRECT_PROVIDER_URL_REQUIRED")
                    checked=valid_date(value(r,"H"))
                    if r.get("H",("",False,""))[1]:
                        raise ValueError("SOURCE_DATE_CELL_FORMULA")
                    if checked<day or checked>datetime.date.today():
                        raise ValueError("SOURCE_CHECK_DATE_INVALID")
                    count["structurally_complete_pairs"]+=1
                    by_league[league]+=1
                except (ValueError,TypeError) as error:
                    count["issues"]+=1
                    if len(problems)<25:problems.append({"sheet":tab,"row":rowno,"code":str(error)})
        if count["old_vendor_one_sided_pairs"]!=56:
            raise ValueError("56_OLD_ONE_SIDED_REFERENCES_CHANGED")
        if count["EKSIK_2026_rows"]+count["EKSIK_2025_rows"]!=1855:
            raise ValueError("1855_BASELINE_NOT_MATCHING")
        return {
          "status":"STRUCTURE_PASS_RESEARCH_ONLY" if count["issues"]==0 else "MANUAL_INPUT_ERRORS",
          "aggregate":dict(sorted(count.items())),
          "structurally_reviewable_by_league":dict(sorted(by_league.items())),
          "sample_issues_max25":problems,
          "source_workbook_modified":False,
          "input_rows_or_xg_values_exported":0,
          "complete_pair_is_not_asof_proof":True,
          "source_license_for_AI_training":"NOT_ESTABLISHED",
          "new_M4_training_rows":0,
          "new_22_league_training_rows":0
        }

def selftest():
    assert xg(("0",False,"n"))==0
    assert xg(("",False,"")) is None
    for cell in (("1,4",False,"s"),("=2+2",True,""),("99",False,"n")):
        try:xg(cell)
        except ValueError:pass
        else:raise AssertionError("invalid input accepted")
    assert valid_date("2026-11-01")==DATE(2026,11,1)
    print("PASS synthetic: blank != zero, formula injection, comma string, outside xG range")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook")
    p.add_argument("--report")
    p.add_argument("--self-test",action="store_true")
    arg=p.parse_args()
    if arg.self_test:selftest()
    if arg.workbook:
        doc=audit(arg.workbook)
        print(json.dumps(doc,indent=2,ensure_ascii=False))
        if arg.report:
            Path(arg.report).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    elif not arg.self_test:p.error("Pass --workbook or --self-test")
