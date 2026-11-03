"""beyondELO 2.6.3: single planned identity and chronology acceptance, NOT a model test.
Source: beyondELO https://beyondelo.com — CC BY 4.0.
"""
import csv, difflib, hashlib, io, json, math, unicodedata, urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

BASE = "https://public-api.beyondelo.com/v1/datasets/"
SOURCES = {"current":"club-ratings.csv",
           "2024-2025":"club-elo-history/2024-2025.csv",
           "2025-2026":"club-elo-history/2025-2026.csv",
           "2026-2027":"club-elo-history/2026-2027.csv"}
COLUMNS = {"current":{"slug","name","country_code","elo","rd","as_of"},
           **{k:{"date","club","elo","rd"} for k in SOURCES if k!="current"}}
COUNTRY = {"BEL1":"BEL","ENG1":"ENG","ENG2":"ENG","ESP1":"ESP",
           "FRA1":"FRA","GER1":"GER","ITA1":"ITA","NED1":"NED",
           "POR1":"POR","TUR1":"TUR"}
OUT = Path("data/europe_staged_263/elo_integrity_acceptance")
IDX = Path("experiments/263/evidence/identity_index_263.json")

def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").casefold().replace("ı","i").replace("ß","ss"))
    return " ".join("".join(c if c.isalnum() else " " for c in s
                            if not unicodedata.combining(c)).split())

def number_ok(r):
    try:
        return math.isfinite(float(r["elo"])) and math.isfinite(float(r["rd"])) and float(r["rd"])>=0
    except (ValueError,TypeError,KeyError): return False

def date_ok(s):
    try: date.fromisoformat(s); return True
    except (TypeError,ValueError): return False

def fetch(k,p):
    url=BASE+p
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"UEFA-263-One-Planned-Integrity-Audit","Accept":"text/csv"})
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(20000001); http=r.status; last=r.headers.get("Last-Modified")
        if http!=200 or not raw or len(raw)>20000000: raise ValueError("HTTP_OR_SIZE_UNSAFE")
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not COLUMNS[k].issubset(set(reader.fieldnames or [])): raise ValueError("CSV_COLUMNS_UNEXPECTED")
        rows=list(reader)
        if not rows: raise ValueError("CSV_EMPTY")
        (OUT/"source_csv").mkdir(parents=True,exist_ok=True)
        (OUT/"source_csv"/(k+".csv")).write_bytes(raw)
        return {"status":"STAGED","url":url,"rows":len(rows),
                "sha256":hashlib.sha256(raw).hexdigest(),"http_last_modified":last},rows
    except Exception as e:
        return {"status":"BLOCKED","url":url,"error_type":type(e).__name__,"message":str(e)[:160]},[]

def identity(current, idx):
    memberships=idx["season_memberships"]["2026-2027"]
    teams={tid:league for league,ids in memberships.items() for tid in ids}
    assert len(teams)==192, "UNEXPECTED_CANONICAL_ID_COUNT"
    aliases=defaultdict(set)
    for alias,tid in idx["aliases"].items():
        if tid in teams: aliases[norm(alias)].add(tid)
    for tid in teams:
        for s in (idx["teams"][tid]["name"],idx["teams"][tid].get("key","")):
            if norm(s): aliases[norm(s)].add(tid)
    rejected=Counter(); samples=[]; candidates=defaultdict(list)
    by_country=defaultdict(list); by_slug=defaultdict(list); as_of=set()
    for line,r in enumerate(current,2):
        slug=(r.get("slug") or "").strip()
        name=(r.get("name") or "").strip()
        country=(r.get("country_code") or "").upper().strip()
        as_of.add(r.get("as_of"))
        if not slug:
            rejected["MISSING_SLUG_WITH_DATA" if any(str(v or "").strip() for v in r.values())
                     else "EMPTY_ROW"]+=1
            if len(samples)<12: samples.append({"line":line,"name":name,"country":country,"reason":"MISSING_SLUG"})
            by_country[country].append({"slug":"","name":name,"usable":False})
            continue
        if not number_ok(r) or not date_ok(r.get("as_of")) or not name or not country:
            rejected["BAD_CURRENT_METADATA"]+=1
            continue
        by_slug[slug].append(r)
        by_country[country].append({"slug":slug,"name":name,"usable":True})
        hits=aliases.get(norm(slug),set())|aliases.get(norm(name),set())
        if len(hits)>1:
            rejected["ALIAS_COLLISION"]+=1; continue
        if len(hits)==1:
            tid=next(iter(hits))
            if COUNTRY[teams[tid]]!=country:
                rejected["COUNTRY_MISMATCH"]+=1
            else: candidates[tid].append(r)
    matched={}; conflicts=[]
    for tid,rows in candidates.items():
        if len(rows)==1 and len(by_slug[rows[0]["slug"]])==1: matched[tid]=rows[0]
        else: conflicts.append({"club":idx["teams"][tid]["name"],"reason":"MULTIPLE_SOURCE_ROWS",
                                "source_names":[r["name"] for r in rows]})
    pending=[]; coverage={}
    for league,tids in sorted(memberships.items()):
        coverage[league]={"total":len(tids),"matched":sum(t in matched for t in tids)}
        for tid in tids:
            if tid in matched: continue
            t=idx["teams"][tid]
            names=[norm(t["name"]),norm(t.get("key",""))]+[
                norm(n) for n,k in idx["aliases"].items() if k==tid]
            suggestions=[]
            for s in by_country[COUNTRY[league]]:
                sim=max((difflib.SequenceMatcher(None,a,b).ratio()
                         for a in names for b in (norm(s["name"]),norm(s["slug"])) if a and b),
                        default=0)
                if sim>=0.54:
                    suggestions.append({"name":s["name"],"slug":s["slug"],
                                        "has_provider_id":s["usable"],
                                        "similarity_only":round(sim,3)})
            suggestions.sort(key=lambda x:(x["similarity_only"],x["has_provider_id"]),reverse=True)
            pending.append({"league":league,"canonical_id":tid,"official_name":t["name"],
                            "official_source":t.get("official_name_source"),
                            "official_url":t.get("official_name_evidence_url"),
                            "status":"REVIEW_NO_GUESSING","unapproved_suggestions":suggestions[:3]})
    return {"total":len(teams),"matched_exact_normalized_name_country_candidates":len(matched),
            "unmatched":len(pending),"coverage":coverage,"pending":pending,
            "matched":[{"id":tid,"name":idx["teams"][tid]["name"],"league":teams[tid],
                        "provider_slug":r["slug"],"provider_name":r["name"],
                        "identity_status":"CANDIDATE_ONLY_NOT_INDEPENDENTLY_VERIFIED"}
                       for tid,r in matched.items()],
            "rejected":dict(rejected),"rejected_samples":samples,
            "multiple_provider_rows":conflicts,
            "repeated_slug_count":sum(len(v)-1 for v in by_slug.values()),
            "source_as_of_dates":sorted(x for x in as_of if x)},matched

def history(tables,matched):
    allkeys=defaultdict(list); stats={}
    for season in ("2024-2025","2025-2026","2026-2027"):
        rows=tables[season]; bad=Counter(); keys=Counter(); ds=[]; clubs=set(); premature=0
        for line,r in enumerate(rows,2):
            c=(r.get("club") or "").strip(); day=(r.get("date") or "").strip()
            if not c:
                bad["EMPTY_CLUB_WITH_DATA" if any(str(v or "").strip() for v in r.values())
                    else "EMPTY_ROW"]+=1; continue
            if not number_ok(r) or not date_ok(day):
                bad["BAD_HISTORY_ROW"]+=1; continue
            ds.append(day); clubs.add(c)
            if day < season[:4]+"-07-01": premature+=1
            keys[(day,c)]+=1
            allkeys[(day,c)].append((season,float(r["elo"]),float(r["rd"]),line))
        stats[season]={"rows":len(rows),"clubs_with_ids":len(clubs),
                       "first":min(ds) if ds else None,"last":max(ds) if ds else None,
                       "duplicate_date_club_extra_rows":sum(n-1 for n in keys.values()),
                       "quarantine":dict(bad),
                       "rows_predating_nominal_july_season_start":premature}
    conflicts=[]; identical_extra=0; safe_by_club=defaultdict(list)
    for (day,club),obs in sorted(allkeys.items()):
        vals={(r[1],r[2]) for r in obs}
        if len(vals)>1:
            conflicts.append({"date":day,"club":club,"values":[
                {"season":s,"elo":e,"rd":rd,"line":line} for s,e,rd,line in obs[:6]],
                "status":"QUARANTINED_NO_SILENT_FIRST_LAST"})
        else:
            identical_extra+=len(obs)-1
            safe_by_club[club].append(day)
    missing=[{"canonical_id":tid,"slug":r["slug"]} for tid,r in matched.items()
             if not safe_by_club.get(r["slug"])]
    return {"per_season":stats,"identical_extra_rows_deduplicated":identical_extra,
            "conflicting_date_club_keys":len(conflicts),"quarantined_conflicts":conflicts,
            "matched_clubs_with_history":len(matched)-len(missing),
            "matched_clubs_without_history":missing,
            "history_has_only_after_match_rating_dates":True,
            "asof_policy":"Choose only observation dates strictly less than fixture local calendar date; never same-day",
            "historical_first_seen_proven":False,
            "caution":"Retrospective series might be backfilled; the archive date is not proof of original public availability."}

def save(filename,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main():
    idx=json.loads(IDX.read_text(encoding="utf-8"))
    src={}; tables={}
    for k,p in SOURCES.items():
        src[k],tables[k]=fetch(k,p)
        print("SOURCE",k,src[k]["status"],src[k].get("rows",0),flush=True)
    report={"schema":"EUROPE_263_IDENTITY_HISTORY_SINGLE_ACCEPTANCE",
            "audited_utc":datetime.now(timezone.utc).isoformat(),
            "source":src,"license":"CC BY 4.0 — beyondELO (https://beyondelo.com)",
            "main_unchanged":True,"model_changed":False,
            "prediction_probability_produced":False,"elo_integration_approved":False}
    matched={}
    if src["current"]["status"]=="STAGED":
        report["identity"],matched=identity(tables["current"],idx)
        save("identity_review_queue.json",report["identity"]["pending"])
    else: report["identity"]={"status":"CURRENT_FILE_BLOCKED"}
    if all(src[s]["status"]=="STAGED" for s in SOURCES if s!="current"):
        report["history"]=history(tables,matched)
    else: report["history"]={"status":"HISTORY_SOURCE_BLOCKED"}
    report["decision"]={"source_snapshots_preserved":all(src[s]["status"]=="STAGED" for s in SOURCES),
        "all_192_verified":False,
        "historical_first_publication_proven":False,
        "model_integration_authorized":False,
        "next_action":"Review identity queue and conflicting historical keys using archived snapshots, without refetching"}
    save("single_integrity_report.json",report)
    print("INTEGRITY_SUMMARY="+json.dumps({
        "snapshot_status":{k:v["status"] for k,v in src.items()},
        "matched":report["identity"].get("matched_exact_normalized_name_country_candidates"),
        "unmatched":report["identity"].get("unmatched"),
        "coverage":report["identity"].get("coverage"),
        "missing_slug":report["identity"].get("rejected",{}).get("MISSING_SLUG_WITH_DATA"),
        "history_duplicates":{k:v["duplicate_date_club_extra_rows"]
            for k,v in report.get("history",{}).get("per_season",{}).items()},
        "history_blank_id":{k:v["quarantine"].get("EMPTY_CLUB_WITH_DATA",0)
            for k,v in report.get("history",{}).get("per_season",{}).items()},
        "history_conflict_keys":report.get("history",{}).get("conflicting_date_club_keys"),
        "elo_model_approved":False},ensure_ascii=False,sort_keys=True),flush=True)
if __name__=="__main__": main()
