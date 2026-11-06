"""One precommitted, persistent Pinnacle h2h call per Turkey day and league.

The workflow MUST git-commit and push a reservation BEFORE invoking collect.
A failed/empty response still consumes the daily reservation. No retries.
This module does not authorize S1/S2 betting and does not alter forecasts.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from datetime import datetime,timezone,date
from pathlib import Path
from zoneinfo import ZoneInfo
from free_bulk_odds_263 import collect,canonical
from market_fifth_baseline_263 import sealed_payload
from sabah_batch_263 import SCHEMA as BATCH_SCHEMA,sha as batch_sha
from sabah_pinnacle_credit_guard_263 import reserve,check_existing,LEAGUES
from pinnacle_market_benchmark_263 import compare,BenchmarkBlocked

TR=ZoneInfo("Europe/Istanbul")
SNAP="SABAH_PINNACLE_SNAPSHOT_V1"

def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def write_new(path,x):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8") as f:
  json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")

def valid_report(report):
 if (report.get("schema")!=BATCH_SCHEMA or
  report.get("payload_sha256")!=batch_sha({k:v for k,v in report.items() if k!="payload_sha256"})):
  raise ValueError("UNSEALED_MORNING_BATCH")
 return report

def eligible(report,root,now):
 valid_report(report)
 if now.tzinfo is None:raise ValueError("AWARE_NOW_REQUIRED")
 day=now.astimezone(TR).date().isoformat()
 if report["day_turkey"]!=day:raise ValueError("NOT_TODAY_TURKEY")
 root=Path(root).resolve()
 leagues=set()
 for row in report["outcomes"]:
  if row["status"]!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
  path=(root/row["forecast_path"]).resolve()
  if not path.is_relative_to(root) or not path.is_file():
   raise ValueError("FORECAST_FILE_NOT_PRESENT")
  f=read(path);sealed_payload(f,"quad_forward_263_v1")
  if row["forecast_sha256"]!=f["payload_sha256"]:raise ValueError("FORECAST_BATCH_SHA_MISMATCH")
  from free_bulk_odds_263 import utc
  created=utc(f["created_at_utc"]);ko=utc(f["fixture"]["kickoff_utc"])
  if created<=now<ko and (now-created).total_seconds()<=600:
   leagues.add(f["fixture"]["league"])
 return sorted(leagues)

def capture(ledger,league,day,out,key,now=None):
 """Only call after a pushed Git reservation, enforced by the workflow."""
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None or day!=now.astimezone(TR).date().isoformat():
  raise ValueError("NOT_TODAY_TURKEY")
 receipt=check_existing(ledger,league,now)
 if receipt is None or receipt.get("status")!="CREDIT_RESERVED_OUTCOME_UNKNOWN":
  raise ValueError("MISSING_PERSISTED_DAILY_RESERVATION")
 if Path(out).exists():raise ValueError("SNAPSHOT_ALREADY_EXISTS_NO_RETRY")
 if not key:raise ValueError("NO_PROVIDER_SECRET_NO_CALL")
 try:
  bulk=collect(date.fromisoformat(day),now,key,bookmaker_filter="pinnacle",
               leagues=(league,),markets=("h2h",))
  state=("BLOCKED_PROVIDER" if bulk.get("blocked") else "OBSERVED_OR_EMPTY")
  reason=bulk.get("blocked",{}).get(league)
 except Exception as exc:
  # After a persistent credit reservation, keep the failure as evidence.
  # Do not expose secret URLs; no second attempt is made.
  state="UNAVAILABLE_NO_RETRY";reason=type(exc).__name__;bulk=None
 record={"schema":SNAP,"league":league,"day_turkey":day,"status":state,
         "reason":reason,"provider":"The Odds API","bookmaker":"pinnacle",
         "market":"h2h","request_made_or_outcome_unknown":True,
         "api_request_attempts_max":1,"retry_automatically":False,
         "reservation":receipt,"observed_at_utc":now.isoformat(),
         "source_bulk":bulk,
         "remaining_credits_as_returned":bulk.get("reported_remaining_credits") if bulk else None,
         "betting_authorized":False,"forecast_unchanged":True}
 record["payload_sha256"]=hashlib.sha256(canonical(record)).hexdigest()
 write_new(out,record)
 return record

def show_mobile(report,root,snap_root):
 valid_report(report);root=Path(root)
 lines=["# Pinnacle sabah bağımsız referans — "+report["day_turkey"],"",
        "Pinnacle, beşinci tahmin modeli değildir. Yalnız geçerli ve aynı-anlı",
        "doğrulanmış MS fiyatları karşılaştırılır. Sabah fiyatı T−60 fiyatı değildir.",""]
 for row in report["outcomes"]:
  if row["status"]!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
  title=row["home"].replace("|","/")+" – "+row["away"].replace("|","/")
  lines+=["## "+title,""]
  league=row["league"];path=Path(snap_root)/report["day_turkey"]/(league+".json")
  if not path.is_file():
   lines+=["- Pinnacle: **YOK / GÜNLÜK SORGU YAPILMADI**",""];continue
  receipt=read(path)
  if receipt.get("schema")!=SNAP or receipt.get("league")!=league or receipt.get("day_turkey")!=report["day_turkey"]:
   raise ValueError("PERSISTED_PRICE_WRONG_LEAGUE_DATE")
  digest=hashlib.sha256(canonical({k:v for k,v in receipt.items() if k!="payload_sha256"})).hexdigest()
  if receipt.get("payload_sha256")!=digest:raise ValueError("PERSISTED_PRICE_SHA_CHANGED")
  if receipt["source_bulk"] is None:
   lines+=["- Pinnacle: **KAYNAK ERİŞİMİ YOK**; tekrar sorgulama yok.",""];continue
  f=read(root/row["forecast_path"])
  try:outcome=compare(f,receipt["source_bulk"])
  except (BenchmarkBlocked,ValueError,KeyError,TypeError) as exc:
   lines+=["- Pinnacle: **EŞLEŞME REDDEDİLDİ** ("+type(exc).__name__+")",""];continue
  if outcome["status"]!="READ_ONLY_SAME_TIME_BENCHMARK":
   lines+=["- Pinnacle: **AYNI ANLI DOĞRULANAMADI** ("+outcome.get("reason","NO_MATCH")+")",""];continue
  p=outcome["pinnacle_no_vig_probabilities"]
  lines+=["- Pinnacle marjsız MS: **1 %{:.1f} · X %{:.1f} · 2 %{:.1f}**".format(
       p["H"]*100,p["D"]*100,p["A"]*100),
       "- Karşılaştırma: **bağımsız araştırma**; S1/S2 değil.",""]
 return "\n".join(lines)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=("eligible","reserve","capture","mobile"))
 p.add_argument("--report");p.add_argument("--root",default=".")
 p.add_argument("--ledger",default="experiments/263/pinnacle_daily_reservations")
 p.add_argument("--snapshots",default="experiments/263/pinnacle_daily_snapshots")
 p.add_argument("--league");p.add_argument("--day");p.add_argument("--out")
 a=p.parse_args();now=datetime.now(timezone.utc)
 if a.mode=="eligible":
  for league in eligible(read(a.report),a.root,now):print(league)
 elif a.mode=="reserve":
  if not a.league or not a.day or now.astimezone(TR).date().isoformat()!=a.day:
   raise SystemExit("INVALID_RESERVATION_DATE")
  path,_=reserve(a.ledger,a.league,now)
  print(path)
 elif a.mode=="capture":
  if not a.league or not a.day or not a.out:raise SystemExit("MISSING_FIELDS")
  # Direct command is unsafe outside the serialized GitHub workflow.
  # The workflow confirms push of reservation before this call.
  capture(a.ledger,a.league,a.day,a.out,os.environ.get("THE_ODDS_API_KEY"),now)
  print("ONE_PINNACLE_ATTEMPT_SAVED",a.league)
 else:
  if not a.report or not a.out:raise SystemExit("MISSING_REPORT")
  text=show_mobile(read(a.report),a.root,a.snapshots)
  path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
  with path.open("x",encoding="utf-8") as f:f.write(text)
if __name__=="__main__":main()
