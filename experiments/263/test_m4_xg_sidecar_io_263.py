"""End-to-end sidecar I/O: xG adds context, sealed M4 stays immutable."""
from __future__ import annotations
import csv
import hashlib
import json
import tempfile
from pathlib import Path

from forward_c3 import canonical_bytes
from m4_integrated import score_markets
from m4_xg_support_263 import sidecar, _sha

def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def run():
    with tempfile.TemporaryDirectory() as folder:
        d=Path(folder); history=d/"history.csv"; xg=d/"private_xg.csv"
        prediction=d/"frozen_forecast.json"; evidence=d/"sidecar.json"
        past=[];private=[]
        for k in range(80):
            day=f"2026-01-{k//28+1:02d}"
            h,a=("H","A") if k%2==0 else ("A","H")
            row={"fixture_id":f"f{k}","league":"ENG1","match_date":day,
                 "home_id":h,"away_id":a,"home_goals":"1","away_goals":"0","result":"H"}
            past.append(row)
            private.append({"fixture_id":row["fixture_id"],"league":"ENG1",
                            "date":day,"home_id":h,"away_id":a,
                            "home_goals":"1","away_goals":"0",
                            "home_xg":"1.8","away_xg":"0.8",
                            "xg_source":"Understat","source_status":"LEGACY_VERIFIED_2026_11_03"})
        write_csv(history,past);write_csv(xg,private)
        m4={"status":"AVAILABLE","goals":score_markets(1.2,1.1)}
        core={"schema":"quad_forward_263_v1","data":{"snapshot_sha256":_sha(history)},
              "fixture":{"league":"ENG1","home_id":"H","away_id":"A",
                         "match_local_date":"2026-02-15"},
              "model_predictions":{"M4":m4}}
        core["payload_sha256"]=hashlib.sha256(canonical_bytes(core)).hexdigest()
        prediction.write_text(json.dumps(core,ensure_ascii=False),encoding="utf-8")
        orig=_sha(prediction);orig_bytes=prediction.read_bytes()
        r=sidecar(prediction,history,xg,evidence)
        assert r["xg"]["status"]=="XG_INCLUDED_IN_M4_RESEARCH_LAMBDA", r
        assert r["forecast_sha256"]==core["payload_sha256"]
        assert _sha(prediction)==orig and prediction.read_bytes()==orig_bytes
        assert r["xg"]["markets"]["M4_original"]==m4["goals"]["markets"]
        assert r["xg"]["markets"]["M4_with_xg"]["OVER_2.5"] != m4["goals"]["markets"]["OVER_2.5"]
        assert evidence.exists() and json.loads(evidence.read_text())["forecast_sha256"]==core["payload_sha256"]
        # No accidental replacement/rewrite of existing sidecar.
        try:sidecar(prediction,history,xg,evidence)
        except FileExistsError:pass
        else:raise AssertionError("existing xG sidecar overwritten")
        # An alternate history must never be paired with the sealed forecast.
        past[0]["home_goals"]="2";write_csv(history,past)
        try:sidecar(prediction,history,xg,d/"must_not_exist.json")
        except ValueError as exc:assert "sha" in str(exc)
        else:raise AssertionError("mismatched history accepted")
        assert not (d/"must_not_exist.json").exists()
    print("PASS: signed historical forecast preserved, xG scored, sidecar immutable, wrong history rejected")

if __name__=="__main__":run()
