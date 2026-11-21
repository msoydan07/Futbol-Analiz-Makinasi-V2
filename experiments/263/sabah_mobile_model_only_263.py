"""Read-only approved mobile PDF from new100 MODEL-ONLY SHA when no user PDF is attached.

No bookmaker API, price search, generated market odds, or market-driven pick.
The user's iddaa.com PDF is handled only by iddaa_pdf_one_step_263.py,
which renders the real first-PDF quote reference.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from sabah_batch_263 import SCHEMA,sha
from sabah_mobile_screens_263 import load_row,decision
from sabah_mobile_approved_pdf_263 import row_data,single_pdf
from iddaa_pdf_approved_layout_263 import render_model_only_batch,LABELS,_p

def build_model_only(report, root="."):
    if (report.get("schema")!=SCHEMA or report.get("cohort")!="new100"
        or report.get("payload_sha256")!=sha(
          {k:v for k,v in report.items() if k!="payload_sha256"})):
        raise ValueError("MODEL_ONLY_UNSEALED_NEW100_REPORT")
    # Not a forged quote: explicit NO PDF observation for every named fixture.
    # Reuse the same immutable forecast/decision view as the PDF writer.
    items=[]
    for r in report["outcomes"]:
        if r.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":
            continue
        f=load_row(root,r)
        d=decision(root,"new100",report["day_turkey"],Path(r["forecast_path"]).stem,f)
        if d is None or d.get("schema")!="263_MODEL_FIRST_FOUR_MODEL_DECISION_RESEARCH_V2":
            raise ValueError("MODEL_ONLY_REQUIRES_CURRENT_EXPERT_DECISION")
        if r.get("decision_sha256")!=d["payload_sha256"]:
            raise ValueError("MODEL_ONLY_DECISION_SHA_MISMATCH")
        items.append({"forecast_path":r["forecast_path"],
                      "forecast_sha256":f["payload_sha256"],
                      "status":"NO_USER_IDDAA_PDF_PRICE_PROVIDED",
                      "reason":"USER_PDF_REQUIRED_FOR_ALL_PRICE_COMPARISONS"})
    neutral={"day_turkey":report["day_turkey"],"cohort":"new100","items":items}
    rows=row_data(report,neutral,root)
    if any(row["market"] is not None or row["delta"] is not None for row in rows):
        raise ValueError("MODEL_ONLY_PDF_CANNOT_CONTAIN_MARKET_PROBABILITIES")
    # Exactly the same screenshot-approved cards as first-iddaa-PDF reports.
    # Use the existing SHA-linked model-first decision, NOT an independently
    # recalculated MS-only guess. The C3 KG/2.5 v4 main pick is preserved.
    source_rows={Path(x["forecast_path"]).stem:x for x in report["outcomes"]
                 if x.get("status")=="REGISTERED_FOUR_MODELS_EXPERIMENTAL"}
    for row in rows:
        src=source_rows.get(row["id"])
        if src is None:raise ValueError("MODEL_ONLY_UNRECOGNIZED_FORECAST")
        f=load_row(root,src)
        d=decision(root,"new100",report["day_turkey"],row["id"],f)
        if (d is None or d.get("payload_sha256")!=src.get("decision_sha256")
            or row.get("decision_sha")!=d["payload_sha256"]
            or row.get("forecast_sha")!=f["payload_sha256"]):
            raise ValueError("MODEL_ONLY_CARD_SHA_MISMATCH")
        main=d.get("main_candidate");alt=d.get("alternative_candidate")
        if main and main.get("market") not in LABELS:
            raise ValueError("MODEL_ONLY_UNKNOWN_MAIN_MARKET")
        if alt and alt.get("market") not in LABELS:
            raise ValueError("MODEL_ONLY_UNKNOWN_ALTERNATIVE_MARKET")
        row["approved_card"]={
            "home":row["home"],"away":row["away"],"league":row["league"],
            "date":report["day_turkey"],"time":row["time"],
            "main":LABELS[main["market"]] if main else "MODEL PAS",
            "ours":_p(main["calibrated_probability"]) if main else "—",
            "fair":"VERİ YOK","diff":"—",
            "alternative":LABELS[alt["market"]]+" "+
              _p(alt.get("calibrated_probability")) if alt else "YOK",
            "main_odds":"—",
            "forecast_sha":f["payload_sha256"],
            "decision_sha":d["payload_sha256"]}
    return rows

def render(report_path, root, output):
    report=json.loads(Path(report_path).read_text(encoding="utf-8"))
    rows=build_model_only(report,root)
    folder=Path(output)
    folder.mkdir(parents=True,exist_ok=True)
    render_model_only_batch(report["day_turkey"],rows,folder/"toplu.pdf")
    detail=folder/"tekli"
    detail.mkdir(exist_ok=True)
    for r in rows:
        single_pdf(detail/(r["id"]+".pdf"),report["day_turkey"],r)
    return {"status":"MODEL_ONLY_MOBILE_PDF_NO_PRICE_SOURCE",
            "source":"NO_IDDAA_PDF_YET","count":len(rows),
            "odds_api_calls":0,"forecast_unchanged":True,
            "pdf_folder":str(folder)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--root",default=".")
    args=ap.parse_args()
    print(json.dumps(render(args.report,args.root,args.out),ensure_ascii=False))

if __name__=="__main__":
    main()
