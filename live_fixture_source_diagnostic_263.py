"""Read-only live visibility check. Zero fixtures must never mean 'parser passed'.
Never archives page bodies, updates prediction data, or guesses kickoff times.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from official_browser_fixture import SOURCES, FALLBACK_SOURCES, discover, extract

TARGETS = {
    "BEL1": [*([SOURCES["BEL1"]]), *FALLBACK_SOURCES.get("BEL1", [])],
    "POR1": [SOURCES["POR1"]],
    "ENG2": [SOURCES["ENG2"], "https://www.efl.com/competitions/efl-championship/"],
}
# These are only hypothetical date windows to probe whether dated fixture
# cards present on today's pages can be parsed beyond an international break.
# They MUST NOT be counted as today's validated seven-day calendar.
REFERENCE_ASOF = {
    "BEL1": datetime(2026, 11, 18, tzinfo=timezone.utc),
    "POR1": datetime(2026, 11, 24, tzinfo=timezone.utc),
    "ENG2": datetime(2026, 11, 18, tzinfo=timezone.utc),
}

def run():
    actual_now = datetime.now(timezone.utc)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        for league, urls in TARGETS.items():
            records = []
            for url in urls:
                page = browser.new_page(locale="fr-BE" if league == "BEL1" else "en-GB")
                rec = {"official_url": url, "http_status": None}
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    rec["http_status"] = response.status if response else 0
                    if rec["http_status"] == 200:
                        page.wait_for_timeout(2200)
                        body = page.locator("body").inner_text(timeout=15000)
                        lines = [x.strip() for x in body.splitlines() if x.strip()]
                        rec["visible_lines"] = len(lines)
                        rec["visible_chars"] = len(body)
                        real = discover(league, lines, actual_now)
                        hypothetical = discover(league, lines, REFERENCE_ASOF[league])
                        rec["real_7day_discover_n"] = len(real)
                        rec["hypothetical_window_discover_n"] = len(hypothetical)
                        rec["hypothetical_window_asof"] = REFERENCE_ASOF[league].isoformat()
                        rec["real_sample"] = [
                            {"home": h, "away": a,
                             "kickoff_utc": extract(league, lines, h, a, actual_now)[0].isoformat()}
                            for h,a in real[:5]
                            if len(extract(league, lines, h, a, actual_now)) == 1
                        ]
                        rec["hypothetical_sample"] = [
                            {"home": h, "away": a,
                             "kickoff_utc": extract(league, lines, h, a, REFERENCE_ASOF[league])[0].isoformat()}
                            for h,a in hypothetical[:5]
                            if len(extract(league, lines, h, a, REFERENCE_ASOF[league])) == 1
                        ]
                        # Small diagnostics only, not full copied webpage content.
                        rec["visible_excerpt"] = lines[:24]
                    else:
                        rec["status"] = "SOURCE_HTTP_FAILURE"
                except Exception as exc:
                    rec["error"] = str(exc)[:150]
                finally:
                    page.close()
                records.append(rec)
            results[league] = records
        browser.close()
    report = {
        "schema": "READ_ONLY_THREE_LEAGUE_FIXTURE_LIVE_SOURCE_DIAGNOSTIC_V1",
        "timestamp_utc": actual_now.isoformat(),
        "today_verified_only_on_matching_source_cards": True,
        "reference_asof_only_diagnostic_not_actual_matchday": True,
        "source_results": results,
        "production_models_or_seals_changed": False,
    }
    out = Path("fixture_diagnostic_20261110.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for league, rows in results.items():
        for row in rows:
            print(json.dumps({
                "league":league,"source":row["official_url"],"http":row["http_status"],
                "lines":row.get("visible_lines"),
                "real_next_7days":row.get("real_7day_discover_n"),
                "hypothetical_future":row.get("hypothetical_window_discover_n"),
                "error":row.get("error"),"sample":row.get("hypothetical_sample",[])[:2],
                "excerpt":row.get("visible_excerpt",[])[:12]
            }, ensure_ascii=False))

if __name__ == "__main__":
    run()
