"""One user action, one iddaa PDF, one black-white analysis PDF.

Never re-scrape prices. Local original PDF remains in private processing
directory; it is NOT committed to GitHub. One official lookup per resolvable
fixture, existing signed B/C2/C3/M4 forecast plus accepted-history baseline,
frozen dev calibration, research-conditional main/alt or PAS.

Example:
  PYTHONPATH=experiments/263 python experiments/263/iddaa_pdf_one_step_263.py \
    --pdf /path/to/user-iddaa.pdf \
    --history /path/to/accepted-history.csv \
    --out-dir /tmp/iddaa-263-sessions

Optional source admission inputs exactly as already required by the 2.6.3
historical data gate: --source-baseline, --source-acceptance.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path

from iddaa_pdf_bulletin_263 import parse_pdf
from iddaa_pdf_session_263 import run_session
from iddaa_pdf_value_bridge_263 import calibrate_session
from iddaa_pdf_report_263 import build as report_pdf

def _write_once(destination,data):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("x",encoding="utf-8") as f:
        json.dump(data,f,sort_keys=True,ensure_ascii=False,indent=2)
        f.write("\n")

def one_step(pdf,*,history,output_root,
             m4_lock="experiments/263/m4_lock.json",
             source_baseline=None,source_acceptance=None,
             dev_lock="experiments/263/forward_dev_calibration_lock_263.json",
             repo_root=".",now=None,official_lookup=None):
    source=Path(pdf)
    if not source.is_file() or not source.suffix.lower()==".pdf":
        raise ValueError("ORIGINAL_USER_IDDAA_PDF_REQUIRED")
    if not Path(history).is_file():
        raise ValueError("ACCEPTED_HISTORICAL_CSV_FILE_REQUIRED")
    bulletin=parse_pdf(source)
    pdf_sha=bulletin["pdf_sha256"]
    folder=Path(output_root)/pdf_sha[:20]
    # One immutable run directory prevents accidental price/prediction rewrite.
    folder.mkdir(parents=True,exist_ok=False)
    copied=folder/"iddaa_original_user.pdf"
    with copied.open("xb") as handle:
        handle.write(source.read_bytes())
    if hashlib.sha256(copied.read_bytes()).hexdigest()!=pdf_sha:
        raise ValueError("COPIED_USER_PDF_SHA_MISMATCH")
    _write_once(folder/"bulletin.json",bulletin)
    options={
        "history":str(history),"lock":str(m4_lock),
        "baseline":str(source_baseline) if source_baseline else None,
        "source_acceptance":str(source_acceptance) if source_acceptance else None,
        "out_dir":str(folder/"forecasts"),
        "empirical_baseline_out_dir":str(folder/"empirical_baselines"),
    }
    session=run_session(bulletin,now=now,official_lookup=official_lookup,
                        forecast_options=options)
    _write_once(folder/"source_session.json",session)
    calibrated=calibrate_session(bulletin,session,
                        original_pdf=copied,repo_root=repo_root,
                        dev_lock_path=dev_lock,now=now)
    _write_once(folder/"calibrated_session.json",calibrated)
    final=report_pdf(calibrated,folder/"futbol_263_iddaa_oranli_rapor.pdf")
    return {
        "status":"LOCAL_IDDAA_PDF_FIRST_SESSION_RESEARCH_COMPLETE",
        "pdf_sha256":pdf_sha,
        "source_rows":bulletin["total_visible_fixtures"],
        "potential_ten_league_rows":bulletin["potential_ten_league_rows"],
        "official_confirmed_rows":session["n_official"],
        "signed_four_model_forecasts":session["n_forecast"],
        "calibrated_price_decisions":calibrated["n_pdf_first_decisions"],
        "research_pas_or_blocked":calibrated["n_pdf_first_pas_or_blocked"],
        "no_bookmaker_api_calls":True,
        "no_old_pilot_changes":True,
        "pdf_report_path":str(final),
        "processing_folder":str(folder),
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pdf",required=True)
    p.add_argument("--history",required=True)
    p.add_argument("--out-dir",default="experiments/263/iddaa_pdf_sessions_263")
    p.add_argument("--m4-lock",default="experiments/263/m4_lock.json")
    p.add_argument("--source-baseline")
    p.add_argument("--source-acceptance")
    p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
    p.add_argument("--repo-root",default=".")
    args=p.parse_args()
    result=one_step(args.pdf,history=args.history,
        output_root=args.out_dir,m4_lock=args.m4_lock,
        source_baseline=args.source_baseline,
        source_acceptance=args.source_acceptance,
        dev_lock=args.dev_lock,repo_root=args.repo_root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
