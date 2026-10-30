"""Audit actual Football-Data results without inventing missing match statistics.

Downloads the same 20 league/season CSVs as the identity pipeline.
Outputs per-source counts and an explicit anomaly report; no predictions.
"""
import csv
import datetime as dt
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path
from collect_team_candidates import LEAGUES, SEASONS, BASE

OUT = Path("data")
RESULTS = {"H", "D", "A"}

def inspect(row):
    home, away, date = ((row.get(k) or "").strip() for k in ("HomeTeam", "AwayTeam", "Date"))
    if not home and not away and not date:
        return "EMPTY", ""
    if not all((home, away, date)) or home == away:
        return "INVALID_IDENTITY", "Missing or identical participants/date"
    try:
        parsed = None
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                parsed = dt.datetime.strptime(date, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError(date)
    except ValueError:
        return "INVALID_DATE", date
    hg, ag, result = ((row.get(k) or "").strip() for k in ("FTHG", "FTAG", "FTR"))
    if not hg and not ag and not result:
        return "UNPLAYED", ""
    if not hg or not ag or result not in RESULTS:
        return "INCOMPLETE_RESULT", f"FTHG={hg}, FTAG={ag}, FTR={result}"
    try:
        if not hg.isascii() or not ag.isascii() or not hg.isdecimal() or not ag.isdecimal():
            raise ValueError("Noninteger score")
        h, a = int(hg), int(ag)
    except ValueError:
        return "INVALID_SCORE", f"{hg}-{ag}"
    expected = "H" if h > a else "A" if a > h else "D"
    if expected != result:
        return "RESULT_MISMATCH", f"{hg}-{ag}, FTR={result}, expected={expected}"
    return "COMPLETE", ""

def main():
    OUT.mkdir(exist_ok=True)
    totals = Counter()
    sources = []
    anomalies = []
    for season, short in SEASONS.items():
        for league, code in LEAGUES.items():
            url = f"{BASE}/{short}/{code}.csv"
            counts = Counter()
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "FutbolAnalizV2/1.0"})
                with urllib.request.urlopen(request, timeout=25) as response:
                    payload = response.read().decode("utf-8-sig", errors="replace")
                reader = csv.DictReader(io.StringIO(payload))
                required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
                if not required.issubset(set(reader.fieldnames or [])):
                    raise ValueError("Missing required columns: " + repr(sorted(required - set(reader.fieldnames or []))))
                for number, row in enumerate(reader, start=2):
                    status, reason = inspect(row)
                    counts[status] += 1
                    totals[status] += 1
                    if status not in ("COMPLETE", "UNPLAYED", "EMPTY"):
                        anomalies.append({"league": league, "season": season, "source_row": number,
                                          "status": status, "detail": reason})
                sources.append({"league": league, "season": season, "url": url,
                                "status": "OK", "counts": dict(counts)})
            except Exception as exc:
                sources.append({"league": league, "season": season, "url": url,
                                "status": "FAILED", "error": str(exc)[:250]})
    report = {"source_count": len(sources), "sources_ok": sum(s["status"] == "OK" for s in sources),
              "totals": dict(totals), "anomaly_count": len(anomalies),
              "anomaly_samples": anomalies[:100], "sources": sources,
              "interpretation": "UNPLAYED is not a missing historical result; data may change between downloads."}
    (OUT / "result_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("anomaly_samples", "sources")}, indent=2))
    if report["sources_ok"] != len(LEAGUES) * len(SEASONS) or anomalies:
        raise SystemExit("Result quality audit failed; inspect result_quality_report.json")

if __name__ == "__main__":
    main()
