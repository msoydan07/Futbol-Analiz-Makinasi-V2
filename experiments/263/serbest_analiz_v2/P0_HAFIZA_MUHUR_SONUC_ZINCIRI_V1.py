#!/usr/bin/env python3
# coding: utf-8
"""Private-input P0/Hafiza -> official-gateway pre-KO receipt -> read-only score comparison.

Receipt creation is possible ONLY after independent 10-league official fixture lookup,
original PDF + mobile staging verification and a future KO check. It is NOT an
official timestamped Git seal until the receipt is committed before kickoff.
Other leagues continue as P0/Hafiza research; no forged official fixture.

No private 35,938-match archive, mobile raw JSON or original PDF is uploaded here.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math,sys
from pathlib import Path
from zoneinfo import ZoneInfo
from MOBIL_HAKEM_STAGING_DOGRULAYICI_V1 import validate as verify_mobile,EVENTS
from HAKEM_PDF_HAFIZA_M4_KOPRU_V1 import _display_label_identity,split_match
from ORAN_TAMAMLAYICI_V1 import read_iddaa_pdf
from GUNLUK_SERBEST_ANALIZ_KAPISI_V2 import gate_result,TZ,TEN_LEAGUES

RECEIPT_SCHEMA="P0_HAFIZA_OFFICIAL_GATE_PREKO_RESEARCH_V1"
RECEIPT_STATUS="GATEWAY_VERIFIED_REQUIRES_GIT_COMMIT_BEFORE_KO"
SCORE_SCHEMA="P0_HAFIZA_EXTERNAL_RESULT_INPUT_V1"
class OddsForwardError(ValueError):pass

def hash_obj(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),
                           ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()

def utc(value):
    if isinstance(value,str):
        value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if value.tzinfo is None:raise OddsForwardError("NAIVE_TIME_FORBIDDEN")
    return value.astimezone(dt.timezone.utc)

def check_receipt(doc, now=None):
    if doc.get("schema")!=RECEIPT_SCHEMA or doc.get("status")!=RECEIPT_STATUS:
        raise OddsForwardError("UNRECOGNIZED_RECEIPT")
    sig=doc.get("payload_sha256")
    if sig!=hash_obj({k:v for k,v in doc.items() if k!="payload_sha256"}):
        raise OddsForwardError("RECEIPT_CONTENT_CHANGED")
    start=utc(doc["kickoff_utc"]);made=utc(doc["observed_at_utc"])
    if made>=start:raise OddsForwardError("POST_KICKOFF_FORECAST_FORBIDDEN")
    if now is not None and utc(now)>=start:
        raise OddsForwardError("NO_NEW_PREKO_COMMIT_AFTER_KICKOFF")
    if doc.get("official_verification")!="OFFICIAL_FIXTURE_GATEWAY_LOOKUP":
        raise OddsForwardError("UNVERIFIED_FIXTURE_PROOF")
    if not str(doc.get("official_source_url","")).startswith("https://"):
        raise OddsForwardError("INVALID_OFFICIAL_SOURCE")
    if not doc.get("fixture_key") or not doc.get("source_pdf_sha256"):
        raise OddsForwardError("MISSING_IDENTITY_OR_PDF")
    return doc

def make_records(staging, raw_pdf, bindings, gateway_lookup, *, now=None):
    """Bindings only select requested rows; they do not authenticate a fixture.
    Gateway callback MUST independently fetch + validate the official page.
    """
    now=utc(now or dt.datetime.now(dt.timezone.utc))
    verify_mobile(staging,raw_pdf)
    # The original bulletin may contain OTHER matches with missing odds.
    # Match each selected mobile row against independent parser evidence by
    # name, clock and ALL SEVEN offered prices; never zip by row index.
    pdf_all=read_iddaa_pdf(raw_pdf)["rows"]
    rows=staging["records"]
    verified_rows=set();seen_pdf=set()
    for n,row in enumerate(rows,1):
        candidates=[]
        for j,pdf_row in enumerate(pdf_all):
            if (pdf_row.get("error") or
                pdf_row.get("time")!=row["kickoff_local_time_user_label"] or
                _display_label_identity(pdf_row.get("match",""))!=
                    _display_label_identity(row["match_name_pdf"])):
                continue
            if all(pdf_row["raw"].get(k) is not None and
                   abs(float(row["seven_raw_odds"][k])-float(pdf_row["raw"][k]))<1e-9
                   for k in EVENTS):
                candidates.append(j)
        if len(candidates)==1 and candidates[0] not in seen_pdf:
            seen_pdf.add(candidates[0]);verified_rows.add(n)
        # Rows which cannot be independently reproduced stay research staging
        # and may NOT enter official-gateway pre-KO receipt creation.
    seen=set();out=[]
    for b in bindings:
        index=b.get("source_row")
        if type(index)!=int or index<1 or index>len(rows) or index in seen:
            raise OddsForwardError("INVALID_OR_DUPLICATE_SOURCE_ROW")
        seen.add(index)
        row=rows[index-1]
        if index not in verified_rows:
            raise OddsForwardError("ORIGINAL_PDF_ROW_NOT_INDEPENDENTLY_REPRODUCIBLE")
        league=b.get("league")
        if league not in TEN_LEAGUES:
            raise OddsForwardError("NO_OFFICIAL_GATE_FOR_LEAGUE_RESEARCH_ONLY")
        expected_date=b.get("date_local_tr")
        if not isinstance(expected_date,str) or not expected_date:
            raise OddsForwardError("LOCAL_TR_DATE_REQUIRED")
        try:dt.date.fromisoformat(expected_date)
        except ValueError as e:raise OddsForwardError("INVALID_LOCAL_DATE") from e
        h,a=split_match(row["match_name_pdf"])
        if ("…" in row["match_name_pdf"] or
            _display_label_identity(h)!=_display_label_identity(b.get("home","")) or
            _display_label_identity(a)!=_display_label_identity(b.get("away",""))):
            raise OddsForwardError("TRUNCATED_OR_DIFFERENT_TEAM_NAME_REVIEW_FIRST")
        official=gateway_lookup(league,b["home"],b["away"])
        checked=gate_result(official,league,now)
        kickoff=utc(checked["kickoff_utc"])
        local_tr=kickoff.astimezone(ZoneInfo("Europe/Istanbul"))
        if (local_tr.date().isoformat()!=expected_date or
            local_tr.strftime("%H:%M")!=row["kickoff_local_time_user_label"]):
            raise OddsForwardError("OFFICIAL_KO_NOT_MATCHING_PDF_DATE_TIME")
        key=hash_obj({"league":league,"home":checked["home_id"],
                      "away":checked["away_id"],"kickoff":checked["kickoff_utc"]})
        original={
            "schema":RECEIPT_SCHEMA,"status":RECEIPT_STATUS,
            "match":b["home"]+" - "+b["away"],"league":league,
            "source_row":index,"fixture_key":key,
            "home_id":checked["home_id"],"away_id":checked["away_id"],
            "kickoff_utc":checked["kickoff_utc"],"observed_at_utc":now.isoformat(),
            "official_source_url":checked["source_url"],
            "official_verification":"OFFICIAL_FIXTURE_GATEWAY_LOOKUP",
            "source_pdf_sha256":staging["source_pdf_sha256"],
            "source_mobile_payload_sha256":staging["staging_payload_sha256"],
            "source_pdf_client_label":row["match_name_pdf"],
            "source_archive_matches":staging["archive_total_matches"],
            "seven_odds":row["seven_raw_odds"],
            "expert_probabilities":{
                "P0":row["p0_seven_proportional"],
                "HAFIZA":row["hafiza_seven_realized"]},
            "hafiza_neighbor_n":row["hafiza_similar_n"],
            "note":"Not a Git seal until accepted by GitHub before kickoff. No M4/Hakem2 forecast invented."
        }
        original["payload_sha256"]=hash_obj(original)
        check_receipt(original,now)
        out.append(original)
    if not out:raise OddsForwardError("NO_GATE_VERIFIED_ROWS")
    if len({x["fixture_key"] for x in out})!=len(out):
        raise OddsForwardError("SAME_OFFICIAL_FIXTURE_USED_TWICE")
    return out

def write_new_records(receipts, folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    files=[]
    for doc in receipts:
        check_receipt(doc,dt.datetime.now(dt.timezone.utc))
        name=doc["kickoff_utc"][:10]+"_"+doc["payload_sha256"][:24]+".json"
        path=folder/name
        with path.open("x",encoding="utf-8") as f:
            json.dump(doc,f,indent=2,ensure_ascii=False,allow_nan=False)
            f.write("\n")
        files.append(str(path))
    return files

def event_truth(home,away):
    if type(home)!=int or type(away)!=int or min(home,away)<0:
        raise OddsForwardError("INVALID_FINAL_SCORE")
    return {
        "MS1":int(home>away),"MSX":int(home==away),"MS2":int(home<away),
        "OVER_2.5":int(home+away>=3),"UNDER_2.5":int(home+away<=2),
        "BTTS_YES":int(home>0 and away>0),
        "BTTS_NO":int(not(home>0 and away>0))
    }

def evaluate_once(receipts, result_input, *, now=None):
    """Score data are externally supplied; this function does NOT verify score provider.
    No output is appended into immutable prediction receipts.
    """
    now=utc(now or dt.datetime.now(dt.timezone.utc))
    if result_input.get("schema")!=SCORE_SCHEMA:
        raise OddsForwardError("INVALID_SCORE_INPUT_SCHEMA")
    by_key={}
    for r in result_input.get("scores",[]):
        k=r.get("fixture_key")
        if not isinstance(k,str) or not k or k in by_key:
            raise OddsForwardError("DUPLICATE_OR_INVALID_SCORE_FIXTURE_KEY")
        by_key[k]=r
    seen=set();report=[]
    for doc in receipts:
        check_receipt(doc)
        k=doc["fixture_key"]
        if k in seen:raise OddsForwardError("DUPLICATE_PREMATCH_FIXTURE")
        seen.add(k)
        ko=utc(doc["kickoff_utc"])
        if now<=ko:
            report.append({"fixture_key":k,"match":doc["match"],"status":"NOT_KICKED_OFF"});continue
        score=by_key.get(k)
        if score is None or score.get("match_status")!="FINAL":
            report.append({"fixture_key":k,"match":doc["match"],"status":"SCORE_NOT_VERIFIED_OR_MISSING"});continue
        if utc(score["observed_after_utc"])<=ko:
            raise OddsForwardError("SCORE_OBSERVED_BEFORE_KICKOFF")
        truth=event_truth(score["home_goals"],score["away_goals"])
        predictions={}
        for source,seven in doc["expert_probabilities"].items():
            p={evt:float(seven[evt]) for evt in EVENTS}
            for family in (EVENTS[:3],EVENTS[3:5],EVENTS[5:7]):
                if abs(sum(p[e] for e in family)-1)>2e-5:
                    raise OddsForwardError("INVALID_RECORDED_MARKET_PROBS")
            pick=max(EVENTS,key=lambda ev:(p[ev],-EVENTS.index(ev)))
            predictions[source]={"pick":pick,"probability":round(p[pick],5),
                                 "correct":bool(truth[pick]),
                                 "family_brier":{
                                     "MS":round(sum((p[e]-truth[e])**2 for e in EVENTS[:3]),6),
                                     "OU25":round(sum((p[e]-truth[e])**2 for e in EVENTS[3:5])/2,6),
                                     "KG":round(sum((p[e]-truth[e])**2 for e in EVENTS[5:7])/2,6)}}
        report.append({"fixture_key":k,"match":doc["match"],
                       "status":"PROVISIONAL_EXTERNAL_SCORE_NOT_INDEPENDENTLY_VERIFIED",
                       "score":str(score["home_goals"])+"-"+str(score["away_goals"]),
                       "picks":predictions})
    done=[r for r in report if r["status"]=="PROVISIONAL_EXTERNAL_SCORE_NOT_INDEPENDENTLY_VERIFIED"]
    return {"schema":"P0_HAFIZA_FORWARD_EVALUATION_READONLY_V1",
            "status":"PROVISIONAL_SCORE_INPUT_REQUIRES_INDEPENDENT_VERIFICATION",
            "records":report,"total":len(report),"provisional_scored":len(done),
            "pending":len(report)-len(done),
            "hit_count":{s:sum(int(x["picks"][s]["correct"]) for x in done if s in x["picks"])
                          for s in ("P0","HAFIZA")},
            "warning":"Scores are input, not independently authenticated here; Git commit before KO must also be checked."}

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    c=sub.add_parser("capture")
    for f in ("staging","pdf","bindings","engine-root","out-dir"):
        c.add_argument("--"+f,required=True,type=Path)
    e=sub.add_parser("evaluate")
    e.add_argument("--receipts-dir",required=True,type=Path)
    e.add_argument("--scores",required=True,type=Path)
    e.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.mode=="capture":
        root=a.engine_root.resolve()
        sys.path.insert(0,str(root/"experiments/263"))
        sys.path.insert(0,str(root))
        from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
        gateway=OfficialFixtureGateway()
        raw=a.pdf.read_bytes()
        stage=json.loads(a.staging.read_text(encoding="utf-8"))
        bindings=json.loads(a.bindings.read_text(encoding="utf-8"))
        if not isinstance(bindings,list):raise OddsForwardError("BINDING_LIST_REQUIRED")
        output=make_records(stage,raw,bindings,gateway.lookup)
        paths=write_new_records(output,a.out_dir)
        print(json.dumps({"status":"NOT_GIT_SEALED_YET","count":len(paths),"files":paths}))
    else:
        rec=[json.loads(p.read_text(encoding="utf-8")) for p in sorted(a.receipts_dir.glob("*.json"))]
        scores=json.loads(a.scores.read_text(encoding="utf-8"))
        result=evaluate_once(rec,scores)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps({"status":result["status"],"scored":result["provisional_scored"],"pending":result["pending"]}))
if __name__=="__main__":main()
