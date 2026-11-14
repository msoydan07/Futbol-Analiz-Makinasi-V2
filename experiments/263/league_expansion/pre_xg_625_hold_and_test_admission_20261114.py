#!/usr/bin/env python3
"""One-pass data preparation only: existing 625 HOLD partitions and test gates.
Reads previous reports and immutable SOURCE POINTER manifest; NEVER fits,
scores, downloads or rewrites a model, sealed pilot, source match or xG.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
R=Path("experiments/263/league_expansion")
def table(name):
 with (R/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def js(name):return json.loads((R/name).read_text(encoding="utf-8"))
BASE="FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json"
PTR="FINAL_9460_SOURCE_ROW_DECISIONS_NO_SCORE_REHOST_20261114.csv"
COR="CORRECTED_200_ENG3_ENG4_SOURCE_POINTERS_NOT_ADDITIVE_20261114.csv"
ENG96="eng5_2025_26_96_exact_original_FT_conflict_training_HOLD_20261114.csv"
RIGHTS="4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json"
HOLD="2396_296_hold_rights_and_feature_vintage_final_20261114.json"
PREV="CROSS_SOURCE_9460_200_IDENTITY_POINTERS_AUDIT_20261114.json"
OUT=R/"625_PRE_XG_DATA_ADMISSION_CONTRACT_20261114.json"
DOC=R/"625_PRE_XG_DATA_ADMISSION_CONTRACT_20261114.md"
CODE={"EXISTING_CORE_4617_FROZEN_RESULTS_ONLY":4617,
"SCORE_FACT_RESEARCH_ONLY_QA_PASS":4218,
"EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD":296,
"EXCLUDED_UNCLEARED_UPSTREAM_RIGHTS":325,
"EXCLUDED_NONLEAGUE_CONFERENCE_PLAYOFF":3,
"EXCLUDED_ABANDONED_NOT_FT":1}
BAD="EXCLUDED_LEGACY_SCORE_OR_DATE_HOLD"
HOLDS=tuple(k for k in CODE if k.startswith("EXCLUDED_"))
def key(parts):return hashlib.sha256("\x1f".join(parts).encode("utf8")).hexdigest()
def utc(text):
 if not isinstance(text,str):raise ValueError("UTC_PROOF_MISSING")
 t=datetime.fromisoformat(text.replace("Z","+00:00"))
 if t.tzinfo is None or t.utcoffset() is None:raise ValueError("NAIVE_TIME")
 return t.astimezone(timezone.utc)
def allowed_prior_feature(r):
 """Synthetic smoke-test, no actual pre-kickoff source receipt is invented."""
 if not r.get("reuse_rights_verified") or not r.get("source_proof"):
  raise ValueError("RIGHTS_OR_PROVENANCE_NOT_VERIFIED")
 if r.get("feature_field","").lower() in {
 "ft_home","ft_away","ht_home","ht_away","xg_home","xg_away",
 "target_result","target_xg","full_time","home_goals","away_goals"}:
  raise ValueError("TARGET_RESULT_FEATURE_LEAK")
 if not r.get("source_match") or r.get("source_match")==r.get("target_match"):
  raise ValueError("SAME_FIXTURE_OR_MISSING")
 completed=utc(r["source_completed_utc"])
 available=utc(r["feature_available_utc"])
 observed=utc(r["snapshot_observed_utc"])
 kickoff=utc(r["target_kickoff_utc"])
 if not completed+timedelta(hours=48)<kickoff:
  raise ValueError("SOURCE_FIXTURE_NOT_48H_PRIOR")
 if not completed<=available<=observed<kickoff:
  raise ValueError("HISTORIC_FEATURE_TIME_LEAK")
 return True
def run():
 base=js(BASE);rights=js(RIGHTS);hold=js(HOLD);prior=js(PREV)
 assert base["source_rows"]==9460 and base["research_score_fact_qa_pass_only"]==4218
 assert base["research_excluded_quality_or_rights"]==625
 assert prior["total_source_rows_referenced"]==9460
 assert prior["exact_cross_source_fixture_duplicates_in_pass"]==0
 assert rights["newly_promoted_to_training"]==0
 assert rights["source_metadata_nonproof_count"]["explicit_precise_prematch_input_proof_present"]==0
 p=table(PTR);assert len(p)==9460
 counts=Counter();hold_ids=defaultdict(set);by_league=defaultdict(Counter)
 by_season=defaultdict(Counter);by_role=Counter();identities=set()
 analysis={"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1","SCO1","DNK1","CHE1"}
 training={"ENG3","ENG4","ENG5","GER2","ESP2","ITA2","FRA2","GRE1","AUT1"}
 assert len(analysis)==13 and len(training)==9 and analysis.isdisjoint(training)
 for x in p:
  status=x["decision"]
  if status not in CODE:raise ValueError("NEW_DISPOSITION")
  ident=(x["source_path"],x["source_row_1based"])
  if ident in identities:raise ValueError("SOURCE_ROW_REPEAT")
  identities.add(ident)
  if x["league"] not in analysis|training or x["season"] not in ("2025-26","2026-27"):
   raise ValueError("SCOPE_DRIFT")
  counts[status]+=1
  by_season[x["season"]][status]+=1
  if status in HOLDS:
   h=x["fixture_key_sha256"]
   if h in hold_ids[status]:raise ValueError("DUPLICATE_HELD_FIXTURE")
   hold_ids[status].add(h)
   by_league[x["league"]][status]+=1
  if status=="SCORE_FACT_RESEARCH_ONLY_QA_PASS":
   by_role["analysis" if x["league"] in analysis else "training_only"]+=1
 assert dict(counts)==CODE
 assert sum(len(v) for v in hold_ids.values())==625
 assert all(not hold_ids[a].intersection(hold_ids[b]) for a in HOLDS for b in HOLDS if a!=b)
 corrected=table(COR)
 assert len(corrected)==200
 old_keys={r["old_bad_fixture_key_sha256"] for r in corrected}
 assert len(old_keys)==200 and old_keys<=hold_ids[BAD]
 assert Counter(r["decision"] for r in corrected)=={
 "VERIFIED_THIRD_SOURCE_SCORE_REPLACEMENT":178,
 "VERIFIED_INDIVIDUAL_DATE_AND_RESULT_REPLACEMENT":22}
 assert all(r["model_training_status"]=="NOT_APPROVED_RIGHTS_ASOF_AND_SPLIT_REQUIRED"
  and r["additive_new_match"]=="NO__SOURCE_POINTER_CORRECTION_NOT_NEW_FIXTURE"
  for r in corrected)
 held=table(ENG96);assert len(held)==96
 ninety_six={key((r["league"],r["season"],r["original_date"],r["home"],r["away"])) for r in held}
 assert len(ninety_six)==96 and ninety_six<=hold_ids[BAD]
 assert old_keys.isdisjoint(ninety_six) and old_keys|ninety_six==hold_ids[BAD]
 assert sum(by_role.values())==4218
 assert sum(by_season[s]["SCORE_FACT_RESEARCH_ONLY_QA_PASS"] for s in ("2025-26","2026-27"))==4218
 assert hold["disjoint_partitions"]["rights_unclear_322_ccby_compilation_plus_3_third_party"]==325
 assert (R/"751_ADAY_KAPSAM_DISI_KARARI_20261114.md").exists()
 result={
 "date":"2026-11-14","cutoff":"2026-11-13",
 "status":"PRE_XG_DATA_ONLY_625_DISPOSITION_AND_TEST_ADMISSION_PREP_DONE",
 "source_pointer_rows_unchanged":9460,"core_results_unchanged":4617,
 "research_score_fact_QA_PASS_LABEL_ONLY":4218,
 "research_HOLD":625,
 "hold_disjoint_counts":{"OLD_ENG3_ENG4_BAD":200,"OLD_ENG5_BAD":96,
 "UNCLEARED_RIGHTS":325,"AUT1_OTHER_COMPETITION_STAGE":3,"FRA2_ABANDONED_NOT_FT":1},
 "hold_counts_by_league":{k:dict(v) for k,v in sorted(by_league.items())},
 "old_200_corrected_only_as_NONADDITIVE_reference":200,
 "old_200_score_only_replacements":178,"old_200_date_and_score_replacements":22,
 "old_ENG5_96_held_not_user_96_sealed_pilot":True,
 "source_rows_promoted_to_training":0,
 "exact_future_feature_receipts_known_for_research":0,
 "corrected_200_pointers_promoted_to_training":0,
 "core_99_old_official_review_incomplete":43,
 "2025_26_vs_2026_27_SCORE_ONLY_NOT_A_SPLIT":{
  s:by_season[s]["SCORE_FACT_RESEARCH_ONLY_QA_PASS"] for s in ("2025-26","2026-27")},
 "analysis_vs_training_only_SCORE_ONLY_NOT_A_SPLIT":dict(by_role),
 "date_leakage_synthetic_contract_passed":True,
 "prediction_accuracy_rerun":False,"new_pilot":False,
 "old_96_real_sealed_pilot_rewritten":False,"old_39_sealed_scoring_repeated":False,
 "model_retrained":False,"M4_unchanged":True,"user_xg_workbook_unchanged":True,
 "new_751_external_candidate_rows":0,
 "today_done":["625 existing exact pointer partitions verified",
  "200 corrected pointer references checked without duplicating matches",
  "96 distinct ENG5 original bad fixtures correctly held",
  "existing 4218 score facts kept distinct from model eligible features",
  "strict feature leakage, UTC timing and data rights guard preregistered",
  "no new mathematical experiment and no old pilot rescoring"],
 "after_xg_external_gates_not_solved_by_xg_alone":[
  "independent source rights for previously collected research labels and features",
  "real historic time-of-availability evidence for retrospective model inputs",
  "43 partially confirmed historical core results if official-grade certification required"],
 "no_automatic_model_ready_claim":True,
 "existing_sealed_96_evaluation_policy":"NO_REWRITE_NO_NEW_PILOT",
 "comparison_prospective_policy":"B/C2/C3/M4 on same sealed fixture cohort; MS/BTTS/2.5 OVER only, performance cannot be interpreted from score-only archive",
 "remaining_user_action":"manual entry of 1855 paired post-match xG values with per-match source",
 }
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 lines=[
 "# 625 kaynak HOLD - xG öncesi veri-kabul hazırlığı",
 "14 Kasım 2026 | Sadece veri mühendisliği | M4 ve eski mühürler dokunulmadı",
 "",
 "## Kesinleşen 625",
 "| Sınıf | Sayı | Sonuç |","|---|---:|---|",
 "| ENG3/ENG4 orijinal hatalı kaynak | 200 | 178 skor + 22 skor/tarih için düzeltme işaretçisi var; eskiler HOLD, yeni maç değil |",
 "| ENG5 orijinal skor/tarih çelişkisi | 96 | Hâlâ HOLD; kullanıcının 96 mühürlü pilotundan tamamen farklı |",
 "| Üst kaynak kullanım hakkı açık değil | 325 | Eğitimden dışarıda |",
 "| Avusturya başka organizasyon | 3 | Lig kümesinden dışarıda |",
 "| Bastia-Red Star oynanmamış 90 dakika FT | 1 | Sonuç etiketi olarak kabul edilmez |",
 "| **Toplam** | **625** | Sınıflandırma kilitli |",
 "",
 "## Deney öncesi veri kalitesi",
 "- 9.460 kaynak işaretçisi, 4.617 eski ana maç ve 4.218 skor-olgu kalite kontrolü sonucu korunur.",
 "- 4.218 araştırma skoru henüz maç önü özelliği ve model eğitim izni değildir.",
 "- Kaynaklarda kesin tarihli gerçek maç-önü özellik görüntüsü sıfırdır. Sonradan girilen xG geçmiş tahminin girdisiymiş gibi kullanılmaz.",
 "- Mevcut 96 SHA mühürlü pilot değiştirilmez; 39 önceki maç sonucu karşılaştırması tekrar yapılmaz.",
 "- Testten önce tarih, gerçek kaynak kullanım hakkı ve aynı 4-model ortak örneklem şartı kontrol edilir. Skor ve xG sadece maç sonu hedeftir.",
 "- 751 kaynak adayı kullanıcının kararına göre kapsam dışı, yeni pilot yok.",
 "",
 "## Senin işin ve sınır",
 "- Sıradaki kullanıcı işi: 1.855 maç için aynı kaynaktan ev/deplasman gerçekleşmiş xG ve maç URL'si.",
 "- Mevcut xG dosyası değiştirilmedi. Hazır salt-okunur xG kontrolcüsüyle daha sonra kontrol edilecek.",
 "- xG bitince eksik kaynak lisansı, 43 resmî teyit ve gerçek tarihli maç önü özellik kanıtı otomatik kapanmış sayılmaz; bunlar ayrıca görünür.",
 "- Bu turda model eğitimi, değerlendirme, karşılaştırma, yeni mühür, kaynak yeniden indirme yapılmadı."
 ]
 DOC.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"source":9460,"holds":625,
 "old_corrected_reference_only":200,"ENG5_bad_hold":96,"train":0,"test":0},ensure_ascii=False))
def tests():
 assert sum(CODE.values())==9460 and sum(CODE[k] for k in HOLDS)==625
 good={"reuse_rights_verified":True,"source_proof":"source_SHA",
 "feature_field":"prior_home_form","source_match":"old","target_match":"new",
 "source_completed_utc":"2026-11-01T18:00:00Z",
 "feature_available_utc":"2026-11-01T19:00:00Z",
 "snapshot_observed_utc":"2026-11-03T00:00:00+00:00",
 "target_kickoff_utc":"2026-11-08T18:00:00Z"}
 assert allowed_prior_feature(good)
 for replacement in [
  {"feature_field":"ft_home"},{"source_match":"new"},{"reuse_rights_verified":False},
  {"source_proof":""},{"feature_available_utc":"2026-11-09T00:00:00Z"},
  {"snapshot_observed_utc":"2026-11-09T00:00:00Z"},
  {"target_kickoff_utc":"2026-11-02T18:00:00Z"},
  {"feature_available_utc":"2026-11-01T19:00:00"}]:
  try:allowed_prior_feature({**good,**replacement})
  except (ValueError,KeyError):pass
  else:raise AssertionError("MISSING_FAIL_CLOSED_GATE")
 print("PASS synthetic frozen 625 totals, UTC leakage, rights, same fixture and postmatch target bans; no model")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--run",action="store_true")
 a=ap.parse_args()
 if a.self_test:tests()
 if a.run:run()
