"""Pin already-generated stage2 development calibration without refitting models."""
import argparse,hashlib,json
from pathlib import Path
from forward_calibration_bridge_263 import lock_from_stage2
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage2",required=True);ap.add_argument("--predictions",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    stage=Path(a.stage2);csv=Path(a.predictions)
    if not stage.is_file() or not csv.is_file():raise SystemExit("SOURCE_ARTIFACT_MISSING")
    report=json.loads(stage.read_text(encoding="utf-8"))
    out=lock_from_stage2(report,source_report_sha256=hashlib.sha256(stage.read_bytes()).hexdigest(),
        source_predictions_sha256=hashlib.sha256(csv.read_bytes()).hexdigest())
    dest=Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps({"lock":str(dest),"sha256":out["payload_sha256"],"models":list(out["calibration"]),
        "markets_per_model":{m:len(c) for m,c in out["calibration"].items()}},sort_keys=True))
if __name__=="__main__":main()
