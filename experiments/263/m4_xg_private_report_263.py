"""Pre-kickoff M4 xG private user-facing comparison. Research-only, no seal changes.

The GitHub Actions runner cannot see ChatGPT Library. Execute this helper only
in an environment where an audited PRIVATE xG CSV was supplied separately,
never in a public checkout or as a repository artifact. Output is a compact
model comparison; raw provider xG values are never printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import tempfile
from pathlib import Path

from forward_c3 import canonical_bytes
from m4_xg_support_263 import sidecar, _sha

DEFAULT_4618_SHA = "3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c"


def as_utc(value):
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("TIMEZONE_AWARE_TIME_REQUIRED")
    return value.astimezone(dt.timezone.utc)


def safe_path(p, forbidden):
    path = Path(p).resolve()
    checkout = Path(forbidden).resolve()
    if path.is_relative_to(checkout):
        raise ValueError("PRIVATE_DATA_OR_EVIDENCE_INSIDE_PUBLIC_REPO")
    return path


def render_compact(data):
    x = data["xg"]
    status = x["status"]
    lines = [
        "# M4 + geçmiş xG / xGA — özel maç önü analiz",
        "",
        "**Durum:** " + status,
        "**Tahmin mührü:** " + data["forecast_sha256"],
        "**Kullanılan geçmiş xG maçı:** " + str(x["used_matches"]),
        "**Tahminin kendi xG'si:** KULLANILMADI",
        "",
    ]
    if status == "XG_INCLUDED_IN_M4_RESEARCH_LAMBDA":
        old = x["markets"]["M4_original"]
        new = x["markets"]["M4_with_xg"]
        pct = lambda n: "%{:.2f}".format(100*n)
        lines.extend([
            "| Pazar | Mevcut M4 | Geçmiş xG katkılı M4 |",
            "|---|---:|---:|",
            "| 2.5 Üst | {} | {} |".format(pct(old["OVER_2.5"]), pct(new["OVER_2.5"])),
            "| 2.5 Alt | {} | {} |".format(pct(old["UNDER_2.5"]), pct(new["UNDER_2.5"])),
            "| KG Var | {} | {} |".format(pct(old["BTTS_YES"]), pct(new["BTTS_YES"])),
            "| KG Yok | {} | {} |".format(pct(old["BTTS_NO"]), pct(new["BTTS_NO"])),
            "| MS1 | {} | {} |".format(pct(old["1X2"]["H"]),pct(new["1X2"]["H"])),
            "| MSX | {} | {} |".format(pct(old["1X2"]["D"]),pct(new["1X2"]["D"])),
            "| MS2 | {} | {} |".format(pct(old["1X2"]["A"]),pct(new["1X2"]["A"])),
            "",
            "**Yorum:** xG'nin geçmiş 1.083 maçta en güçlü işareti 2.5 Alt/Üst pazarındaydı.",
            "KG ve MS değişimleri araştırma bilgisidir; otomatik üstün model/EV kararı değildir.",
            "xG en son kullanılan maç tarihi: " + str(x["last_used_date"]),
        ])
    else:
        lines.append("**Karar:** Geçerli geçmiş xG katkısı bulunamadı; M4 orijinal hesabı korundu.")
        lines.append("Neden: " + str(x.get("reason", "kaynak/rol geçmişi yetersiz")))
    lines.extend([
        "",
        "**Güvenlik:** xG yalnızca geçmiş maçlardan; orijinal SHA tahmini ve mevcut fiyat/PAS kararı değişmedi.",
        "**Sınır:** Bu rapor gerçek resmî bahis onayı veya kârlılık garantisi değildir.",
    ])
    return "\n".join(lines) + "\n"


def produce(*, forecast_path, history_path, private_xg_path,
            evidence_path, expected_xg_sha=DEFAULT_4618_SHA, now=None,
            public_repo_dir="."):
    now = as_utc(now or dt.datetime.now(dt.timezone.utc))
    xg_path = safe_path(private_xg_path, public_repo_dir)
    evidence = safe_path(evidence_path, public_repo_dir)
    if not re.fullmatch(r"[a-f0-9]{64}", str(expected_xg_sha)):
        raise ValueError("INVALID_XG_EXPECTED_SHA")
    if _sha(xg_path) != expected_xg_sha:
        raise ValueError("PRIVATE_XG_SHA_MISMATCH")
    fpath = Path(forecast_path)
    original = fpath.read_bytes()
    forecast = json.loads(original)
    if forecast.get("schema") != "quad_forward_263_v1":
        raise ValueError("WRONG_FORECAST_SCHEMA")
    if forecast.get("fixture", {}).get("fixture_verification") != "VERIFIED_BY_LIVE_OFFICIAL_GATE":
        raise ValueError("OFFICIAL_FIXTURE_GATE_NOT_VERIFIED")
    kickoff = as_utc(forecast["fixture"]["kickoff_utc"])
    created = as_utc(forecast["created_at_utc"])
    if not created <= now < kickoff:
        raise ValueError("NOT_PREKICKOFF_CANNOT_CREATE_SIDE_REPORT")
    if _sha(history_path) != forecast["data"]["snapshot_sha256"]:
        raise ValueError("ACCEPTED_SCORE_HISTORY_SHA_MISMATCH")
    payload = dict(forecast)
    seal = payload.pop("payload_sha256", None)
    if not seal or hashlib.sha256(canonical_bytes(payload)).hexdigest() != seal:
        raise ValueError("FORECAST_SEAL_MISMATCH")
    out = sidecar(forecast_path, history_path, xg_path, evidence)
    if fpath.read_bytes() != original:
        raise RuntimeError("ORIGINAL_M4_FORECAST_CHANGED")
    return render_compact(out)


def main():
    parser = argparse.ArgumentParser(description="Private M4 + xG pre-kickoff report, no write to GitHub.")
    for flag in ("forecast", "history", "xg", "out"):
        parser.add_argument("--"+flag, required=True)
    parser.add_argument("--expected-xg-sha", default=DEFAULT_4618_SHA)
    parser.add_argument("--public-repo-dir", default=".")
    args = parser.parse_args()
    report = produce(forecast_path=args.forecast, history_path=args.history,
                     private_xg_path=args.xg, evidence_path=args.out,
                     expected_xg_sha=args.expected_xg_sha,
                     public_repo_dir=args.public_repo_dir)
    print(report)


if __name__ == "__main__":
    main()
