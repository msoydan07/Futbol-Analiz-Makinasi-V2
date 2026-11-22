"""One-time source audit for existing local SHA-locked 23-match research archive.

Important: the original user PDF and research SHA-lock were generated in the
local chat container, not by this GitHub runner. This tool CANNOT retroactively
turn that research record into an original canonical official model seal.
It ONLY time-stamps independent official-fixture evidence before kickoff.
"""
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from iddaa_pdf_official_lookup_batch_263 import OriginalPdfOfficialGateway

TR=ZoneInfo("Europe/Istanbul")
DATE="2026-11-22"
OUT=Path("/tmp/20261122_23_match_original_official_source_evidence.json")
# Original bulletin list; exact kickoff clocks are from user's eight iddaa PDFs.
MATCHES=[
("ENG1","Hull City","Brighton & Hove Albion","17:00"),
("ENG1","Liverpool","Manchester United","19:30"),
("GER1","Augsburg","Mainz","17:30"),
("GER1","Werder Bremen","Hamburg","19:30"),
("NED1","Ajax","ADO Den Haag","16:30"),
("NED1","Sparta Rotterdam","AZ Alkmaar","16:30"),
("NED1","Go Ahead Eagles","Fortuna Sittard","18:45"),
("ESP1","Barcelona","Villarreal","16:00"),
("ESP1","R. Racing Club","Real Sociedad","18:15"),
("ESP1","Osasuna","Malaga CF","20:30"),
("ESP1","Getafe","Atletico Madrid","23:00"),
("ITA1","Bologna","Udinese","17:00"),
("ITA1","Sassuolo","Genoa","17:00"),
("ITA1","Milan","Frosinone","20:00"),
("ITA1","Atalanta","Inter","22:45"),
("FRA1","Paris FC","Angers","17:00"),
("FRA1","Lorient","Rennes","19:15"),
("FRA1","Marseille","Le Mans","22:45"),
("ENG2","Burnley","Blackburn Rovers","15:00"),
("BEL1","SK Beveren","KAA Gent","15:30"),
("BEL1","Kortrijk","Union Saint-Gilloise","18:00"),
("BEL1","Anderlecht","O.H. Leuven","20:30"),
("BEL1","Lommel SK","Standard de Liège","21:15")
]
assert len(MATCHES)==23 and len(set(MATCHES))==23
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
def main():
    g=OriginalPdfOfficialGateway()
    result={"schema":"NOV22_23_OFFICIAL_SOURCE_AUDIT_ONLY_V1",
            "request":"Check SHA-research records' independent source quality before kickoff",
            "official_forecast_seals_created":0,"canonical_first_pdf_reprocessed":False,
            "original_pdf_bytes_retrieved_in_runner":False,
            "prior_research_SHA_kept_untouched":True,
            "records":[]}
    try:
        for league,home,away,t in MATCHES:
            now=datetime.now(timezone.utc)
            ko=datetime.fromisoformat(DATE+"T"+t+":00").replace(
                tzinfo=TR).astimezone(timezone.utc)
            row={"league":league,"home":home,"away":away,
                 "user_pdf_kickoff_tr":t,"user_pdf_kickoff_utc":ko.isoformat(),
                 "checked_at_utc":now.isoformat(),
                 "official_source_verification":"NOT_ATTEMPTED",
                 "sealing_allowed":False}
            if now>=ko:
                row["official_source_verification"]="KICKOFF_PASSED_BEFORE_CHECK"
            else:
                try:
                    observed=g.lookup(league,home,away)
                    diagnostics=g.gateway.latest_match_evidence(league,home,away)
                    row["source_diagnostics"]=diagnostics
                    if observed.get("status")=="VERIFIED_OFFICIAL_FIXTURE":
                        obs=datetime.fromisoformat(observed["kickoff_utc"].replace("Z","+00:00"))
                        if obs.astimezone(timezone.utc)==ko:
                            row["official_source_verification"]="VERIFIED_SAME_IDENTITY_DATE_TIME"
                            row["official_source_url"]=observed["source_url"]
                            row["official_kickoff_utc"]=observed["kickoff_utc"]
                            row["official_observed_utc"]=observed["retrieved_at_utc"]
                        else:
                            row["official_source_verification"]="OFFICIAL_PDF_KICKOFF_DISAGREEMENT"
                            row["official_kickoff_utc"]=observed["kickoff_utc"]
                    else:
                        row["official_source_verification"]="NOT_VERIFIED"
                        row["source_reason"]=observed.get("reason")
                except Exception as exc:
                    row["official_source_verification"]="GATE_ERROR"
                    row["source_reason"]=type(exc).__name__+":"+str(exc)[:110]
            row["record_sha256"]=hashlib.sha256(canonical(row)).hexdigest()
            result["records"].append(row)
            print("PREMATCH_SOURCE_AUDIT",json.dumps({
                k:row[k] for k in ("league","home","away","user_pdf_kickoff_tr",
                "official_source_verification")},ensure_ascii=False),flush=True)
    finally:
        result["completed_at_utc"]=datetime.now(timezone.utc).isoformat()
        statuses={}
        for row in result["records"]:
            k=row["official_source_verification"]
            statuses[k]=statuses.get(k,0)+1
        result["counts"]=statuses
        result["batch_sha256"]=hashlib.sha256(canonical(result)).hexdigest()
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
        print("FINAL_23_OFFICIAL_SOURCE_AUDIT",json.dumps({
            "n":len(result["records"]),"counts":statuses,
            "canonical_official_forecast_sha_created":False,
            "source_evidence_sha256":result["batch_sha256"]},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
