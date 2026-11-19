#!/usr/bin/env python3
"""2.6.3: ONE morning model seal; ONE append-only pre-kickoff football review.

Actual input: ORIGINAL completed iddaa PDF-first session, SECOND user iddaa
PDF, and OPTIONAL independently researched, time-stamped XI observations.
Never fit/retrain models, update forecasts, recalculate value picks, call odds
APIs, fetch news or create a second model seal. Unverified evidence => silence.
The 2nd PDF is human-supplied source material, never independently fetched.
"""
from __future__ import annotations
import argparse,hashlib,json,math,shutil
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from iddaa_pdf_bulletin_263 import parse_pdf,SCHEMA as PDF_SCHEMA
from iddaa_pdf_session_263 import SCHEMA as MORNING_SCHEMA,market_no_vig,PDF_TO_MARKET
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label
from iddaa_pdf_first_quote_263 import sha256,utc

SCHEMA="263_SINGLE_MORNING_SEAL_ONE_PREKO_REVIEW_V1"
FIELDS=("MS1","MSX","MS2","OVER_2.5","UNDER_2.5","BTTS_YES","BTTS_NO")
FAMILY={"MS":"MS","GOALS_2.5":"GOALS_2.5","KG":"KG"}
XI_STATUSES={"CONFIRMED","PREDICTED","UNKNOWN"}
CATEGORIES={"GOALKEEPER","DEFENCE","MIDFIELD","ATTACK","FORMATION","ROTATION","WEATHER"}
SIDES={"HOME","AWAY"}
AFFECT={"POSSIBLE_ATTACK_RISK","POSSIBLE_DEFENCE_RISK","POSSIBLE_TACTICAL_CHANGE","NO_QUANTIFIED_EFFECT"}
def source_url(s):
 if not isinstance(s,str) or len(s)>600:return False
 try:
  v=urlsplit(s)
  return (v.scheme=="https" and bool(v.hostname) and v.username is None and
          v.password is None and v.port is None and bool(v.path and v.path!="/"))
 except ValueError:return False
def _unique_xi(xs):
 return (isinstance(xs,list) and len(xs)==11 and
         all(isinstance(v,str) and 2<=len(v.strip())<=120 for v in xs)
         and len({v.strip().casefold() for v in xs})==11)
def _hash_file(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _read(p):
 return json.loads(Path(p).read_text(encoding="utf-8"))
def _write_once(p,obj):
 with Path(p).open("x",encoding="utf-8") as f:
  json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
  f.write("\n")
def _id(r):
 return (r["league"],r["home_id"],r["away_id"],r["match_date_tr"])
def _last_key(p,resolver):
 if p.get("league") is None or p.get("status")!="PDF_ROW_READY_FOR_ONE_OFFICIAL_FIXTURE_CHECK":
  return None
 a=resolver(p["league"],p["home_label"])
 b=resolver(p["league"],p["away_label"])
 if not a or not b or a==b:return None
 return (p["league"],a,b,p["match_date_tr"])
def _xi_record(e,m,now,ko):
 """Input is a source claim; NEVER assert source content was re-fetched here."""
 empty={"status":"KADRO_KANITI_YOK","comments":[],"independently_verified_by_script":False}
 if not isinstance(e,dict):return empty
 identity=(e.get("league"),e.get("home_id"),e.get("away_id"),e.get("match_date_tr"))
 if identity!=_id(m) or e.get("lineup_status")!="CONFIRMED":
  return {**empty,"status":"KADRO_KIMLIGI_VEYA_DOGRULAMASI_YETERSIZ"}
 try:
  checked=utc(e["observed_at_utc"])
  if not (checked<=now<ko) or now-checked>timedelta(minutes=100):
   raise ValueError("STALE_OR_LATE_XI")
  if not source_url(e["source_url"]) or not _unique_xi(e.get("home_starting_xi")) or not _unique_xi(e.get("away_starting_xi")):
   raise ValueError("UNUSABLE_XI")
 except (KeyError,ValueError,TypeError):
  return {**empty,"status":"KADRO_KAYNAGI_VEYA_SAATI_YETERSIZ"}
 # A lineup supplied with URL/time is still an UNVERIFIED SOURCE CLAIM.
 out={"status":"XI_KAYNAK_IDDIASI_KAYDEDILDI","source_url":e["source_url"],
      "observed_at_utc":checked.isoformat(),"home_starting_xi":e["home_starting_xi"],
      "away_starting_xi":e["away_starting_xi"],"comments":[],
      "independently_verified_by_script":False}
 reviews=e.get("observations",[])
 if not isinstance(reviews,list) or len(reviews)>12:
  return {**out,"status":"YORUM_FORMATI_YETERSIZ"}
 for r in reviews:
  if not isinstance(r,dict):continue
  fact=r.get("fact");reason=r.get("football_reason");src=r.get("source_url")
  if (r.get("side") not in SIDES or r.get("category") not in CATEGORIES or
      r.get("impact") not in AFFECT or not source_url(src) or
      not isinstance(fact,str) or not 8<=len(fact.strip())<=250 or
      not isinstance(reason,str) or not 8<=len(reason.strip())<=250):
   continue
  # Prevent fabricated "new since morning" without a morning source receipt.
  compare=r.get("morning_comparison")
  if compare is None:
   freshness="SABAH_KIYASI_YOK_YENI_GELISME_DENEMEZ"
  elif isinstance(compare,dict) and source_url(compare.get("source_url")) and isinstance(compare.get("fact"),str) and compare["fact"]:
   try:
    cmoment=utc(compare.get("observed_at_utc"))
    if cmoment>utc(m["price_capture_utc"]):continue
   except (ValueError,TypeError):continue
   freshness="SABAH_KAYNAK_ATFI_VAR_MANUEL_KIYAS_GEREKIR"
  else:continue
  # No numerical model adjustment, no causal inference from odds movement.
  out["comments"].append({"side":r["side"],"category":r["category"],
      "fact":fact.strip(),"football_reason":reason.strip(),
      "impact":r["impact"],"source_url":src,"freshness":freshness,
      "source_verified_by_program":False})
 return out

def build(morning,first,last,xi_evidence,now,*,resolver):
 """One pass over morning matches; no new model calls. Returns one review."""
 now=utc(now.isoformat()) if isinstance(now,datetime) else utc(now)
 if (morning.get("schema")!=MORNING_SCHEMA or first.get("schema")!=PDF_SCHEMA or
     last.get("schema")!=PDF_SCHEMA or
     first.get("pdf_sha256")!=morning.get("pdf_sha256") or
     morning.get("source_bookmaker")!="iddaa.com" or
     first.get("source_domain")!="iddaa.com" or last.get("source_domain")!="iddaa.com" or
     morning.get("bookmaker_reverification_calls")!=0):
  raise ValueError("MORNING_OR_SECOND_PDF_SOURCE_INVALID")
 s=morning.get("signed_research_session_sha256")
 if not isinstance(s,str) or s!=sha256({k:v for k,v in morning.items() if k!="signed_research_session_sha256"}):
  raise ValueError("MORNING_MATHEMATICAL_RECORD_SHA_TAMPERED")
 initial=utc(first["pdf_capture_utc"]);late=utc(last["pdf_capture_utc"])
 if not initial<=utc(morning["session_created_utc"])<late<=now:
  raise ValueError("PDF_DATE_ORDER_INVALID_OR_SECOND_NOT_LATER")
 if now-late>timedelta(minutes=35):
  raise ValueError("SECOND_PDF_STALE_RECAPTURE_AND_REVIEW")
 evidence=xi_evidence or []
 if not isinstance(evidence,list) or len(evidence)>100:raise ValueError("LINEUP_EVIDENCE_MUST_BE_LIST")
 by_evidence=defaultdict(list)
 for e in evidence:
  if not isinstance(e,dict):raise ValueError("INVALID_LINEUP_EVIDENCE")
  key=(e.get("league"),e.get("home_id"),e.get("away_id"),e.get("match_date_tr"))
  by_evidence[key].append(e)
 idx=defaultdict(list)
 for r in last["rows"]:
  k=_last_key(r,resolver)
  if k:idx[k].append(r)
 rows=[]
 for m in morning["rows"]:
  if m.get("status")!="FOUR_MODELS_FORECAST_SHA_CREATED" or m.get("model_forecast_created") is not True:
   continue
  if not isinstance(m.get("model_forecast_sha256"),str) or len(m["model_forecast_sha256"])!=64:
   raise ValueError("ORIGINAL_MODEL_SHA_NOT_PRESENT")
  key=_id(m);ko=utc(m["official"]["kickoff_utc"])
  if not utc(m["price_capture_utc"])<ko:
   raise ValueError("MORNING_TIME_NOT_PRE_MATCH")
  r={"league":m["league"],"home":m["pdf_home"],"away":m["pdf_away"],
     "home_id":m["home_id"],"away_id":m["away_id"],
     "match_date_tr":m["match_date_tr"],"kickoff_time_tr":m["kickoff_time_tr"],
     "kickoff_utc":ko.isoformat(),"morning_model_sha256":m["model_forecast_sha256"],
     "morning_models_not_recalculated":True,
     "morning_model_probabilities":m.get("model_1x2_and_core_markets",{}),
     "morning_odds":m.get("prices",{}),
     "latest_odds":None,"market_no_vig_change_pp":{},
     "lineups":{"status":"KADRO_KANITI_YOK","comments":[]},
     "status":"INCELEME_BEKLIYOR"}
  if now>=ko or late>=ko:
   r["status"]="MAC_BASLADI_VEYA_GUNCEL_PDF_GEC_KALDI";rows.append(r);continue
  if (ko-now)>timedelta(minutes=120):
   r["status"]="ILK11_PENCERESI_HENUZ_ACILMADI";rows.append(r);continue
  matches=idx.get(key,[])
  if len(matches)!=1:
   r["status"]="GUNCEL_PDF_MAC_ESLESMEDI" if not matches else "GUNCEL_PDF_CIFT_KAYIT";rows.append(r);continue
  p=matches[0]
  if (p.get("match_date_tr"),p.get("kickoff_time_tr"))!=(m["match_date_tr"],m["kickoff_time_tr"]):
   r["status"]="GUNCEL_PDF_KICKOFF_DEGISTI_YENI_RES_MI_KONTROL_GEREK";rows.append(r);continue
  r["latest_odds"]={name:p["odds"][pdfkey] for pdfkey,name in PDF_TO_MARKET.items()
                    if p["odds"] is not None and p["odds"].get(pdfkey) is not None}
  newfair=market_no_vig(p);oldfair=m.get("market_no_vig") or {}
  for group in FAMILY:
   a=oldfair.get(group,{})
   b=newfair.get(group,{})
   if (a.get("status")=="FULL_MARKET_QUOTE_AVAILABLE" and
       b.get("status")=="FULL_MARKET_QUOTE_AVAILABLE"):
    r["market_no_vig_change_pp"][group]={
       market:round(100*(newvalue-a["no_vig"][market]),2)
       for market,newvalue in b["no_vig"].items() if market in a.get("no_vig",{})}
  if len(by_evidence.get(key,[]))==1:
   r["lineups"]=_xi_record(by_evidence[key][0],m,now,ko)
  elif len(by_evidence.get(key,[]))>1:
   r["lineups"]={"status":"CIFT_KADRO_KAYNAGI_CELISKISI","comments":[]}
  r["status"]="GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR"
  rows.append(r)
 return {"schema":SCHEMA,"morning_pdf_sha256":first["pdf_sha256"],
  "morning_session_sha256":s,"second_pdf_sha256":last["pdf_sha256"],
  "morning_observed_utc":initial.isoformat(),"last_odds_observed_utc":late.isoformat(),
  "reviewed_at_utc":now.isoformat(),"matches_reviewed":len(rows),
  "rows":rows,"math_refitted":False,"forecast_shas_replaced":False,
  "second_model_seal_created":False,"bookmaker_network_calls":0,
  "independent_lineup_source_fetch_by_program":False,
  "football_commentary_source_claims_not_automatic_verification":True,
  "betting_authorized":False}

def summary_md(review):
 lines=["# 2.6.3 — TOPLU SON FUTBOL KONTROLÜ","",
  "Tek sabah matematik mührü korunmuştur. Bu bir **ikinci tahmin/mühür değildir**.",
  "Son PDF: "+review["last_odds_observed_utc"]+" (UTC).",
  "**Kural:** Oran oynadı diye model yüzdesi değişmez. Kadro kaynakları kod tarafından internette doğrulanmış sayılmaz.",
  "",
  "| Maç | Sabah → Son MS 1 | Oran durumu | İlk 11 / futbol yorumu |",
  "|---|---|---|---|"]
 for r in review["rows"]:
  def price(v):return ("%.2f"%v) if isinstance(v,(int,float)) and not isinstance(v,bool) else "—"
  before=r["morning_odds"].get("MS1")
  after=(r["latest_odds"] or {}).get("MS1")
  status=r["lineups"]["status"]
  lines.append("| "+r["home"].replace("|","/")+" – "+r["away"].replace("|","/")+
   " | "+price(before)+" → "+price(after)+" | "+r["status"]+" | "+status+" |")
 lines+=["","## Yedi pazarın ilk/son oranı ve donmuş M4 yüzdeleri",""]
 for r in review["rows"]:
  lines.append("### "+r["home"].replace("|","/")+" – "+r["away"].replace("|","/"))
  m=r.get("morning_model_probabilities",{}).get("M4",{})
  last=r.get("latest_odds") or {}
  for label,k in (("MS1","MS1"),("MSX","MSX"),("MS2","MS2"),("KG Var","BTTS_YES"),("KG Yok","BTTS_NO"),("2.5 Üst","OVER_2.5"),("2.5 Alt","UNDER_2.5")):
   p=m.get(k)
   mp=("%.1f%%"%(100*p)) if isinstance(p,(int,float)) and not isinstance(p,bool) and 0<=p<=1 else "—"
   lines.append("- "+label+": "+str(r["morning_odds"].get(k,"—"))+" → "+str(last.get(k,"—"))+"; mühürlü M4 "+mp)
  pp=r.get("market_no_vig_change_pp") or {}
  if pp:lines.append("- Marjsız piyasa yüzde puan farkı (son - sabah): "+", ".join(k+" "+str(v) for fam in pp.values() for k,v in fam.items()))
 lines+=["","## Kaynaklı notlar (yüzdeye dokunulmadı)",""]
 for r in review["rows"]:
  if r["lineups"].get("comments"):
   lines.append("### "+r["home"]+" – "+r["away"])
   for x in r["lineups"]["comments"]:
    lines.append("- **Kaynakla ilişkilendirilmiş gözlem (doğrudan otomatik doğrulanmadı):** "+
     x["fact"].replace("\n"," ")+" — **Olası futbol etkisi, sayısal değil:** "+
     x["football_reason"].replace("\n"," ")+" ([kaynak]("+x["source_url"]+")). "+
     "Sabah karşılaştırması: "+x["freshness"]+".")
 if not any(r["lineups"].get("comments") for r in review["rows"]):
  lines.append("Güvenilir yorum için yeterli kanıt aktarılmadı. **Yorum uydurulmadı.**")
 lines+=["","**Not:** Belirsiz kadro, eşleşmeyen PDF veya başlamış maç için yeni tahmin yaratılmaz; önceki mühür olduğu gibi kalır."]
 return "\n".join(lines)+"\n"

def render_pdf(review,target):
 """Phone-readable monochrome second REVIEW PDF; never a model forecast."""
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 from reportlab.lib.pagesizes import A4
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
 from reportlab.lib import colors
 p=Path(target)
 if p.exists():raise FileExistsError("FINAL_REVIEW_PDF_IMMUTABLE")
 paths=("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
 for name,f in zip(("ReviewNormal","ReviewBold"),paths):
  if not Path(f).is_file():raise ValueError("UNICODE_FONT_MISSING")
  pdfmetrics.registerFont(TTFont(name,f))
 small=ParagraphStyle("small",fontName="ReviewNormal",fontSize=8.4,leading=12)
 heading=ParagraphStyle("heading",fontName="ReviewBold",fontSize=11,leading=15)
 title=ParagraphStyle("title",fontName="ReviewBold",fontSize=14,leading=18)
 story=[Paragraph("2.6.3 - MAC ONU TOPLU FUTBOL KONTROLU",title),
  Spacer(1,8),Paragraph("Tek sabah matematik muhru korunur. Ikinci model tahmini YOK.",small),
  Paragraph("Son oran PDF zamani (UTC): "+escape(review["last_odds_observed_utc"]),small),
  Spacer(1,12)]
 for row in review["rows"]:
  def fmt(v):return "%.2f"%v if isinstance(v,(int,float)) and not isinstance(v,bool) else "-"
  last=row.get("latest_odds") or {}
  parts=[Paragraph(escape(row["home"]+" - "+row["away"]),heading),
   Paragraph("Durum: "+escape(row["status"]),small),
   Paragraph("Kadro: "+escape(row["lineups"]["status"]),small)]
  m4=row.get("morning_model_probabilities",{}).get("M4",{})
  for label,key in (("MS 1","MS1"),("MS X","MSX"),("MS 2","MS2"),("2.5 Ust","OVER_2.5"),("2.5 Alt","UNDER_2.5"),("KG Var","BTTS_YES"),("KG Yok","BTTS_NO")):
   q=m4.get(key)
   pct=("%.1f%%"%(100*q)) if isinstance(q,(int,float)) and not isinstance(q,bool) and math.isfinite(q) and 0<=q<=1 else "-"
   parts.append(Paragraph(escape(label+": "+fmt(row["morning_odds"].get(key))+" -> "+fmt(last.get(key))+" | sabit M4 "+pct),small))
  comments=row["lineups"].get("comments",[])
  if comments:
   for c in comments:
    parts.append(Paragraph(escape(c["fact"]+" | "+c["football_reason"]),small))
    parts.append(Paragraph("Kaynak: "+escape(c["source_url"]),small))
  parts.append(Spacer(1,12))
  story.append(KeepTogether(parts))
 story.append(Paragraph("Yorumlar dogrudan otomatik internette dogrulanmis sayilmaz; "
   "oran hareketinden mac sonucu veya sayisal etki cikarilmadi.",small))
 doc=SimpleDocTemplate(str(p),pagesize=A4,leftMargin=32,rightMargin=32,
   topMargin=32,bottomMargin=32,title="2.6.3 Son Futbol Kontrolu")
 doc.build(story)
 return p

def process(morning_dir,second_pdf,xi_json=None,now=None):
 """The sole optional last-minute addendum per original completed PDF session."""
 from iddaa_pdf_one_step_263 import _prior_completed_session
 folder=Path(morning_dir).resolve()
 receipt=_read(folder/"completed_receipt.json")
 original_sha=receipt.get("pdf_sha256")
 # This verifies the morning PDF, report and session receipt without re-fit.
 _prior_completed_session(folder,original_sha)
 old=_read(folder/"calibrated_session.json")
 first=_read(folder/"bulletin.json")
 original=folder/"iddaa_original_user.pdf"
 if first.get("pdf_sha256")!=_hash_file(original):
  raise ValueError("MORNING_ORIGINAL_PDF_CHANGED")
 second=Path(second_pdf)
 if second.suffix.lower()!=".pdf":raise ValueError("SECOND_USER_IDDAA_PDF_REQUIRED")
 actual_second_sha=_hash_file(second)
 target=folder/"last_football_review"
 if target.exists():
  report=_read(target/"review.json")
  if (report.get("second_pdf_sha256")!=actual_second_sha or
      report.get("morning_session_sha256")!=old.get("signed_research_session_sha256") or
      report.get("morning_pdf_sha256")!=original_sha or
      not (target/"summary.md").is_file() or not (target/"review.pdf").is_file()):
   raise ValueError("SECOND_REVIEW_ALREADY_DONE_OR_INCOMPLETE_NO_REPEAT")
  return {"status":"EXISTING_SAME_SECOND_PDF_REVIEW","already_reviewed":True,
          "pdf_report":str(target/"review.pdf"),"summary":str(target/"summary.md")}
 last=parse_pdf(second)  # real user's second PDF; no synthetic quote source
 if last["pdf_sha256"]!=actual_second_sha:raise ValueError("SECOND_PDF_BYTES_CHANGED")
 evidence=_read(xi_json) if xi_json else []
 if not isinstance(evidence,list):raise ValueError("XI_JSON_LIST_REQUIRED")
 ix,_,_=index_registry()
 def resolver(l,n):
  d=resolve_label(l,n,ix)
  return d.get("team_id") if isinstance(d,dict) else None
 review=build(old,first,last,evidence,now or datetime.now(timezone.utc),resolver=resolver)
 # If no official morning seal exists, no second work is pretended.
 if not review["rows"]:raise ValueError("NO_ORIGINAL_SIGNED_MORNING_MATCHES")
 # No post-kickoff fresh "pre-match" review for that game's observation.
 if not any(r["status"]=="GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR" for r in review["rows"]):
  raise ValueError("NO_MATCH_WITH_SAFE_PREKICKOFF_SECOND_PDF")
 target.mkdir(parents=False,exist_ok=False)
 _write_once(target/"review.json",review)
 with (target/"summary.md").open("x",encoding="utf-8") as f:f.write(summary_md(review))
 render_pdf(review,target/"review.pdf")
 return {"status":"ONE_FINAL_REVIEW_ATTACHED_TO_ORIGINAL_SEAL","already_reviewed":False,
         "matches":review["matches_reviewed"],
         "pdf_report":str(target/"review.pdf"),
         "summary":str(target/"summary.md")}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--morning-dir",required=True)
 p.add_argument("--second-iddaa-pdf",required=True)
 p.add_argument("--lineups-json",help="Optional source-evidenced XI observations; no fabricated commentary")
 a=p.parse_args()
 print(json.dumps(process(a.morning_dir,a.second_iddaa_pdf,a.lineups_json),
                  ensure_ascii=False,indent=2))
if __name__=="__main__":main()
