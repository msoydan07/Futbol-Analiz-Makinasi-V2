"""Read-only Elo source acceptance. Not a prediction or model approval."""
import csv,io,json,hashlib,math,re,unicodedata,urllib.request,urllib.error
from datetime import datetime,timezone,date
from pathlib import Path
from collections import defaultdict
BASE="https://public-api.beyondelo.com/v1/datasets/"
FILES={"club-ratings.csv":{"slug","name","country_code","elo","rd","as_of"},
       **{"club-elo-history/"+s+".csv":{"date","club","elo","rd"}
          for s in ("2024-2025","2025-2026","2026-2027")}}
def norm(s):
    s=unicodedata.normalize("NFKC",s).casefold()
    s="".join(c for c in unicodedata.normalize("NFKD",s) if not unicodedata.combining(c))
    return " ".join(s.split())
def fetch(path):
    url=BASE+path
    req=urllib.request.Request(url,headers={"Accept":"text/csv","User-Agent":"UEFA-263-Elo-ReadOnly-Source-Audit"})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            raw=response.read(50000001)
            media=response.headers.get("Content-Type","")
            last_modified=response.headers.get("Last-Modified")
            status=response.status
        if len(raw)>50000000 or not raw or status!=200: raise ValueError("BAD_HTTP_SIZE")
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not reader.fieldnames or not FILES[path].issubset(set(reader.fieldnames)):
            raise ValueError("REQUIRED_CSV_COLUMNS_MISSING")
        rows=list(reader)
        if not rows:raise ValueError("EMPTY_CSV")
        for r in rows:
            if not math.isfinite(float(r["elo"])) or not math.isfinite(float(r["rd"])) or float(r["rd"])<0:
                raise ValueError("INVALID_ELO_OR_RD")
            date.fromisoformat(r["as_of"] if path=="club-ratings.csv" else r["date"])
        return {"status":"FETCHED_AND_SCHEMA_VALID","rows":len(rows),
                "sha256":hashlib.sha256(raw).hexdigest(),"url":url,
                "last_modified":last_modified,"media":media},rows
    except Exception as exc:
        return {"status":"NOT_ACCEPTED","url":url,"error_type":type(exc).__name__,
                "http_error":getattr(exc,"code",None),"detail":str(exc)[:160]},[]
def main():
    source={};data={}
    for p in FILES:
        source[p],data[p]=fetch(p)
        print("ELO_SOURCE",p,source[p]["status"],source[p].get("rows",0),
              source[p].get("error_type",""),flush=True)
    index=json.loads(Path("experiments/263/evidence/identity_index_263.json").read_text(encoding="utf-8"))
    memberships=index["season_memberships"]["2026-2027"]
    clubs={tid:league for league,tids in memberships.items() for tid in tids}
    exact={};ambiguous=set()
    for row in data["club-ratings.csv"]:
        ids={index["aliases"][norm(s)] for s in (row["slug"],row["name"]) if norm(s) in index["aliases"]}
        if len(ids)!=1:continue
        tid=next(iter(ids))
        if tid in ambiguous:continue
        if tid in exact:
            exact.pop(tid,None);ambiguous.add(tid)
        else:exact[tid]=row
    matched={k:v for k,v in exact.items() if k in clubs}
    coverage={league:{"total":len(ids),"exact_alias_candidates":sum(tid in matched for tid in ids),
                      "unmatched_sample":[index["teams"][tid]["name"] for tid in ids if tid not in matched][:8]}
              for league,ids in memberships.items()}
    history={}
    for s in ("2024-2025","2025-2026","2026-2027"):
        rows=data["club-elo-history/"+s+".csv"]
        slugs={r["club"] for r in rows}
        history[s]={"rows":len(rows),"distinct_clubs":len(slugs),
                    "earliest":min((r["date"] for r in rows),default=None),
                    "latest":max((r["date"] for r in rows),default=None),
                    "matched_2026_27_club_slugs":len(slugs & {x["slug"] for x in matched.values()}),
                    "duplicate_date_club":len(rows)-len({(r["date"],r["club"]) for r in rows})}
    samples={}
    for name in ("galatasaray","liverpool"):
        found=[(tid,r) for tid,r in matched.items() if name in norm(index["teams"][tid]["name"])]
        samples[name]=[{"club":index["teams"][tid]["name"],"slug":r["slug"],
                        "snapshot_as_of":r["as_of"],"elo":r["elo"],"rd":r["rd"],
                        "historical_observations":{s:sum(x["club"]==r["slug"] and x["date"]<"2026-11-03"
                              for x in data["club-elo-history/"+s+".csv"]) for s in history}}
                        for tid,r in found]
    accepted=all(source[p]["status"]=="FETCHED_AND_SCHEMA_VALID"
                 for p in ("club-ratings.csv","club-elo-history/2025-2026.csv","club-elo-history/2026-2027.csv"))
    report={"status":"SOURCE_AND_SCHEMA_AUDIT_ONLY_NO_FORECAST_PERMISSION",
            "audited_at_utc":datetime.now(timezone.utc).isoformat(),
            "sources":source,"current_ten_league_teams":len(clubs),
            "current_exact_identity_candidates":len(matched),
            "ambiguous_identity_count":len(ambiguous),
            "coverage_by_league":coverage,"history":history,
            "illustrative_teams":samples,"source_technically_usable":accepted,
            "prediction_model_approved":False,
            "cautions":["Historical CSV date is not an original first_seen timestamp",
                        "Only rows strictly before kickoff date are safe by default",
                        "Exact text alias is a candidate, not independently verified club ID",
                        "International Elo needs validation before modifying goal lambda",
                        "Domestic-only Elo per league is not cross-league comparable",
                        "No betting, pilot, model fitting, domestic code or main change"],
            "license":"CC BY 4.0 attribution beyondELO https://beyondelo.com"}
    out=Path("data/europe_staged_263/elo_source_one_shot_2026_11_03.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("ELO_ACCEPTANCE_SUMMARY="+json.dumps({"accepted":accepted,
          "exact_teams":len(matched),"total_teams":len(clubs),
          "history":history,"samples":samples},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
