"""Conservative one-shot supplement to immutable 4509 research snapshot.

Produces a *staged* 4518-row view, never the accepted pilot history.
Missing source_row and non-comparable match statistics remain blank rather than invented.
"""
from __future__ import annotations
import csv
import hashlib
import json
import uuid
from datetime import date
from pathlib import Path

PINNED="69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14"
NAMESPACE=uuid.UUID("0c312c79-42d1-4ca9-8b1c-4c65b96ef6b2")
DATE="2026-11-03"
LEAGUE="ENG2"

def build(history, manifest, identity_index, out_dir, refs88, refs8):
    history=Path(history); out_dir=Path(out_dir)
    if hashlib.sha256(history.read_bytes()).hexdigest()!=PINNED:
        raise ValueError("PINNED_4509_SHA_CHANGED")
    with history.open(encoding="utf-8-sig",newline="") as f:
        source=list(csv.DictReader(f));fieldnames=list(source[0])
    if len(source)!=4509 or len({r["fixture_id"] for r in source})!=4509:
        raise ValueError("ORIGINAL_4509_NOT_INTACT")
    m=json.loads(Path(manifest).read_text(encoding="utf-8"))
    idx=json.loads(Path(identity_index).read_text(encoding="utf-8"))
    if m.get("schema")!="263_nov3_eng2_manual_independent_score_reference_v1" or m.get("status")!="WEB_CROSSCHECKED_RESEARCH_STAGE_NOT_HUMAN_ACCEPTED" or m.get("date")!=DATE or m.get("league")!=LEAGUE or len(m.get("matches",[]))!=9:
        raise ValueError("UNEXPECTED_SOURCE_MANIFEST")
    if len({s.get("url") for s in m.get("sources",[])})<2:
        raise ValueError("INDEPENDENT_SOURCE_LINKS_MISSING")
    ref88=json.loads(Path(refs88).read_text(encoding="utf-8"))["rows"]
    base_by_id={r["fixture_id"]:r for r in source}
    if len(ref88)!=88 or len({r["fixture_id"] for r in ref88})!=88:
        raise ValueError("88_SOURCE_REFS_INVALID")
    for r in ref88:
        x=base_by_id.get(r["fixture_id"])
        if x is None or any(x[k]!=str(v) for k,v in {"league":r["league"],"match_date":r["match_date"],"home_id":r["home_id"],"away_id":r["away_id"]}.items()) or f'{x["home_goals"]}-{x["away_goals"]}'!=r["source_score"]:
            raise ValueError("PREVIOUS_88_SOURCE_MISMATCH")
    recent=json.loads(Path(refs8).read_text(encoding="utf-8"))["results"]
    if len(recent)!=8:raise ValueError("LAST_8_EVIDENCE_MISSING")
    used=set()
    for r in recent:
        match=[x for x in source if (x["league"],x["match_date"],x["home_goals"],x["away_goals"])==(r["league"],r["date"],str(r["home_goals"]),str(r["away_goals"]))]
        if len(match)!=1 or match[0]["fixture_id"] in used:
            raise ValueError("LAST_8_SCORE_MISMATCH_OR_AMBIGUITY")
        used.add(match[0]["fixture_id"])
    ids=set(base_by_id)
    pairings={(r["league"],r["season"],r["home_id"],r["away_id"]) for r in source}
    additions=[]
    for match in m["matches"]:
        home=idx["aliases"].get(match["home"].lower())
        away=idx["aliases"].get(match["away"].lower())
        if not home or not away or home==away:raise ValueError("TEAM_IDENTITY_NOT_APPROVED")
        h,a=match["hg"],match["ag"]
        if type(h)!=int or type(a)!=int or not (0<=h<=40 and 0<=a<=40):
            raise ValueError("INVALID_MANUAL_SCORE")
        key=("ENG2","2026-2027",home,away)
        id=str(uuid.uuid5(NAMESPACE,"dated-league-fixture:"+json.dumps(list(key),ensure_ascii=False)))
        if key in pairings or id in ids:raise ValueError("DUPLICATE_OR_FROZEN_FIXTURE")
        pairings.add(key);ids.add(id)
        row={k:"" for k in fieldnames}
        row.update(fixture_id=id,league="ENG2",season="2026-2027",match_date=DATE,
                   home_id=home,away_id=away,home_goals=str(h),away_goals=str(a),
                   result="H" if h>a else "D" if h==a else "A",
                   # DO NOT claim to know the provider's CSV line number.
                   source_row="",source_url=m["sources"][0]["url"])
        additions.append(row)
    if len(additions)!=9:raise ValueError("EXPECTED_NINE_NEW_RESULTS")
    if out_dir.exists():raise ValueError("NEVER_OVERWRITE_STAGE_OUTPUT")
    out_dir.mkdir(parents=True)
    dest=out_dir/"extended_history.csv"
    with dest.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,lineterminator="\n")
        writer.writeheader();writer.writerows(source+additions)
    with dest.open(encoding="utf-8",newline="") as f:
        verify=list(csv.DictReader(f))
    if verify[:4509]!=source or len(verify)!=4518 or len({r["fixture_id"] for r in verify})!=4518:
        raise ValueError("STAGE_APPEND_INTEGRITY_FAILED")
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    report={"schema":"263_4518_manual_supplement_research_stage_v1",
        "status":"STAGED_CROSSCHECKED_NOT_HUMAN_ACCEPTED",
        "source_4509_sha256":PINNED,"stage_4518_sha256":digest,
        "source_original_rows_untouched":4509,"added_confirmed_finished_scores":9,
        "ENG2_latest_result_date":DATE,"source_88_reference_consistent":True,
        "source_last_8_reference_consistent":True,
        "source_urls":[x["url"] for x in m["sources"]],
        "added_fixture_ids":[x["fixture_id"] for x in additions],
        "official_100_match_pilot_increment":0,"human_acceptance":False,
        "auto_acceptance":False,"published_to_main":False,
        "provider_csv_source_rows_not_fabricated":True,
        "model_results_recomputed":False}
    (out_dir/"stage_report.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--history",required=True)
    p.add_argument("--manifest",default="data/staged_263/2026_11_03_eng2_9_sources.json")
    p.add_argument("--identity",default="experiments/263/evidence/identity_index_263.json")
    p.add_argument("--refs88",default="data/staged_263/2026_10_30_11_01_previous_88_web_score_refs.json")
    p.add_argument("--refs8",default="data/staged_263/2026_11_05_8_fresh_results_crosscheck.json")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=build(a.history,a.manifest,a.identity,a.output,a.refs88,a.refs8)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
