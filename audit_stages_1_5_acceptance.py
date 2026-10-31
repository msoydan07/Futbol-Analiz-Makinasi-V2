"""Evidence-based acceptance report for stages 1-5; no invented pass statuses."""
import csv,json,sys
from pathlib import Path
P=Path("data")
def load_csv(name):
 p=P/name
 if not p.exists():return None
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def load_json(name):
 p=P/name
 return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
def gate(name,passed,evidence,missing=None):
 return {"stage":name,"status":"PASS" if passed else "NOT_ACCEPTED","evidence":evidence,"remaining":missing or []}
def main():
 h=load_csv("historical_results.csv") or []
 x=load_csv("historical_verified_xg.csv") or []
 source=load_csv("source_audit.csv") or []
 fixtures=load_csv("fixture_candidates.csv") or []
 hist=load_json("historical_results_audit.json") or {}
 missing=load_json("missing_data_inventory_262.json") or {}
 verified=load_json("historical_verified_xg_report.json") or {}
 registry=load_json("match_registry.json") or {}
 ids={r["fixture_id"] for r in h}
 league_seasons={(r["league"],r["season"]) for r in h}
 one=len(ids)==len(h) and len(h)>0 and len(registry.get("fixtures",{}))==len(h) and len(league_seasons)==20
 two=len(source)==20 and all(r["status"]=="OK" for r in source) and bool(missing) and bool(verified)
 three=bool(hist.get("accepted")) and len(h)==hist.get("linked") and len(x)==verified.get("verified_xg_rows") and len(league_seasons)==20
 four=three and len(ids)==len(h) and all(r["fixture_id"] in ids for r in x) and not hist.get("errors") and hist.get("distinct_fixture_ids")==len(h)
 # A seven-day fixture source must include explicitly future, not-yet-played fixtures,
 # verified league/club names, dates, kickoffs and an audit timestamp. Historical results
 # or candidates do not qualify. No such verified module is currently implemented.
 five=False
 stages=[
 gate("01 Kimlikler",one,{"historical_fixtures":len(h),"unique_fixture_ids":len(ids),"registry_fixtures":len(registry.get("fixtures",{})),"league_seasons":len(league_seasons)},[] if one else ["Kimlik/fixture tutarliligini dogrula"]),
 gate("02 Veri envanteri",two,{"sources_ok":sum(r["status"]=="OK" for r in source),"source_total":len(source),"missing_data_inventory_exists":bool(missing),"xg_report_exists":bool(verified)},[] if two else ["20 kaynak ve eksik veri envanterini tamamla"]),
 gate("03 Iki sezon veri",three,{"historical_matches":len(h),"verified_xg_matches":len(x),"league_seasons":len(league_seasons)},[] if three else ["Kaynak kabulunu ve tarihsel veriyi dogrula"]),
 gate("04 Veri kabul",four,{"historical_audit_accepted":hist.get("accepted",False),"historical_audit_errors":hist.get("errors",[]),"xg_ids_linked":all(r["fixture_id"] in ids for r in x)},[] if four else ["Kimlik, skor ve xG baglantisini yeniden denetle"]),
 gate("05 Yedi gunluk fikstur",five,{"verified_future_fixture_feed":False,"fixture_candidates_are_historical":True},["Resmi veya bagimsiz guvenilir gelecek fikstur kaynagi","Takim kimlikleriyle esleme","Saat dilimi ve kaynak zaman damgasi","7 gunluk pencere, tekrar ve kaynak uyusmazligi kabul testi"])
 ]
 out={"version":"stages_1_5_acceptance_v1","policy":"PASS requires evidence, not only green GitHub Actions","stages":stages,"all_accepted":all(x["status"]=="PASS" for x in stages)}
 P.mkdir(exist_ok=True)
 (P/"stages_1_5_acceptance.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
