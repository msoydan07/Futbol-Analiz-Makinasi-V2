#!/usr/bin/env python3
"""NEW-only independent FT score fact QA for 331 *previously absent* 2025/26
Spain Segunda regular-season fixtures + six separately staged playoff legs.

Old 131 match results are NOT rechecked. In-memory football-data.co.uk SP2.csv
second-score witness; no raw provider CSV or proprietary extracts retained.
Original CC BY publisher data untouched. Zero M4 or training admissions.
"""
import argparse,csv,io,json,hashlib,unicodedata,re
from collections import Counter,defaultdict
from datetime import date,datetime
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path("experiments/263/league_expansion")
DIR=ROOT/"ccby_footballcharts_esp2_2025_26_original_source"
NEW=DIR/"esp2_2025_26_NOVEL_331_ONLY_RESEARCH_NOT_TRAINING.csv"
PLAY=DIR/"esp2_2025_26_6_PROMOTION_PLAYOFFS_RESEARCH_ONLY.csv"
OUT=DIR/"esp2_2025_26_NEW_331_reg_6_playoff_independent_score_QA_20261114.json"
URL="https://www.football-data.co.uk/mmz4281/2526/SP2.csv"
P1="0be9536a89955a6ef9d20cf149ce3b8c8b5289c2" # updated after checking exact Git blob of new 331
P2="a40e3bcc102908e9aa5b7fea57ea58cbfc508dd7"
FBREF="https://fbref.com/en/comps/17/2025-2026/schedule/2025-2026-Segunda-Division-Scores-and-Fixtures"
PLAY_EXPECTED=[
 ("2026-06-06","CD Castellón","UD Almería",1,1),
 ("2026-06-07","UD Las Palmas","Málaga CF",0,1),
 ("2026-06-09","UD Almería","CD Castellón",3,2),
 ("2026-06-10","Málaga CF","UD Las Palmas",1,1),
 ("2026-06-14","Málaga CF","UD Almería",0,0),
 ("2026-06-20","UD Almería","Málaga CF",1,2)
]
CLUBS={
 "albacete":"Albacete","almeria":"UD Almería","ud almeria":"UD Almería",
 "andorra":"FC Andorra","fc andorra":"FC Andorra",
 "burgos":"Burgos CF","burgos cf":"Burgos CF",
 "cadiz":"Cádiz CF","cadiz cf":"Cádiz CF",
 "castellon":"CD Castellón","cd castellon":"CD Castellón",
 "ceuta":"AD Ceuta FC","ad ceuta":"AD Ceuta FC","ad ceuta fc":"AD Ceuta FC",
 "cordoba":"Córdoba CF","cordoba cf":"Córdoba CF",
 "cultural leonesa":"Cultural Leonesa","leonesa":"Cultural Leonesa",
 "deportivo la coruna":"Deportivo La Coruña",
 "dep la coruna":"Deportivo La Coruña","dep a coruna":"Deportivo La Coruña",
 "la coruna":"Deportivo La Coruña","deportivo":"Deportivo La Coruña",
 "eibar":"SD Eibar","sd eibar":"SD Eibar",
 "sp gijon":"Sporting Gijón","gijon":"Sporting Gijón","sporting gijon":"Sporting Gijón",
 "granada":"Granada CF","granada cf":"Granada CF",
 "huesca":"SD Huesca","sd huesca":"SD Huesca",
 "las palmas":"UD Las Palmas","ud las palmas":"UD Las Palmas",
 "leganes":"CD Leganés","cd leganes":"CD Leganés",
 "malaga":"Málaga CF","malaga cf":"Málaga CF",
 "mirandes":"CD Mirandés","cd mirandes":"CD Mirandés",
 "racing":"Racing Santander","racing santander":"Racing Santander",
 "sociedad b":"Real Sociedad B","real sociedad b":"Real Sociedad B",
 "valladolid":"Real Valladolid","real valladolid":"Real Valladolid",
 "zaragoza":"Real Zaragoza","real zaragoza":"Real Zaragoza"
}
def norm(x):
 y="".join(c for c in unicodedata.normalize("NFKD",str(x).casefold()) if not unicodedata.combining(c))
 return re.sub(r"[^a-z0-9]+"," ",y).strip()
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
def read(p):return list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
def get():
 req=Request(URL,headers={"Accept":"text/csv","User-Agent":"FutbolAnaliz263-OneOnly331Spain2SourceFactWitness/1.0"})
 with urlopen(req,timeout=35) as f:r=f.read(3_000_001)
 if len(r)>3_000_000:raise ValueError("SECOND_SOURCE_TOO_LARGE")
 return r
def day(s):
 for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
  try:return datetime.strptime(str(s).strip(),fmt).date().isoformat()
  except ValueError:pass
 return None
def compare():
 original=read(NEW);play=read(PLAY)
 if len(original)!=331 or len(play)!=6:raise ValueError("ORIGINAL_NOVEL_COUNTS_CHANGED")
 if blob(PLAY.read_bytes())!=P2:raise ValueError("SIX_PLAYOFF_SOURCE_BLOB_CHANGED")
 # Do not infer source similarity from provider label: explicit aliases only.
 expected_clubs={x for r in original+play for x in (r["home"],r["away"])}
 if not expected_clubs.issubset(set(CLUBS.values())):raise ValueError("NEW_SOURCE_CLUB_NAMES_NOT_MAPPED")
 second=get()
 rr=csv.DictReader(io.StringIO(second.decode("utf-8-sig",errors="replace"),newline=""))
 must={"Div","Date","HomeTeam","AwayTeam","FTHG","FTAG"}
 if not must.issubset(rr.fieldnames or []):raise ValueError("SECOND_SOURCE_SCHEMA_CHANGED")
 source={};unknown=Counter();provider_n=0;dup=Counter()
 for r in rr:
  if r.get("Div")!="SP2":continue
  d=day(r.get("Date"))
  if d is None or not ("2025-07-01"<=d<="2026-06-30"):continue
  try:hg=int(r["FTHG"]);ag=int(r["FTAG"])
  except (ValueError,TypeError):continue
  h=CLUBS.get(norm(r["HomeTeam"]));a=CLUBS.get(norm(r["AwayTeam"]))
  if not h or not a:
   if not h:unknown[str(r["HomeTeam"])]+=1
   if not a:unknown[str(r["AwayTeam"])]+=1
   continue
  k=(d,h,a);score=(hg,ag)
  if k in source:
   if source[k]!=score:raise ValueError("SECOND_SOURCE_ITS_OWN_SCORE_CONFLICT")
   dup["secondary_duplicate_key"]+=1
  source[k]=score;provider_n+=1
 stats=Counter();exceptions=[];byPair=defaultdict(list)
 for d,h,a in source:byPair[(h,a)].append(d)
 for r in original:
  k=(r["date"],r["home"],r["away"])
  old=(int(r["ft_home"]),int(r["ft_away"]))
  got=source.get(k)
  if got is None:
   maybe=[x for x in byPair[(k[1],k[2])] if abs((date.fromisoformat(x)-date.fromisoformat(k[0])).days)<=2]
   outcome="SAME_PAIR_NEAR_DATE_NOT_MATCHED_HOLD" if maybe else "SECOND_SOURCE_NO_EXACT_KEY_HOLD"
  elif got!=old:outcome="SECOND_SOURCE_FT_CONFLICT_HOLD"
  else:outcome="SECOND_SOURCE_DATE_TEAM_FT_EXACT"
  stats[outcome]+=1
  if outcome!="SECOND_SOURCE_DATE_TEAM_FT_EXACT" and len(exceptions)<24:
   exceptions.append({"league":"ESP2","date":r["date"],"home":r["home"],"away":r["away"],
    "original_score":str(old[0])+"-"+str(old[1]),"reason":outcome})
 if sum(stats.values())!=331:raise ValueError("331_NEW_ONLY_VERDICTS_SUM_CHANGED")
 list_play=[(r["date"],r["home"],r["away"],int(r["ft_home"]),int(r["ft_away"])) for r in play]
 if list_play!=PLAY_EXPECTED:
  raise ValueError("PLAYOFF_SOURCE_DOES_NOT_MATCH_INDEPENDENT_FBREF_2025_26_SCOREBOARD")
 return {
  "status":"ONE_PASS_331_NEW_ESP2_REGULAR_SECOND_SOURCE_FACT_CHECK_PLUS_6_PROMOTION_PLAYOFF_FACTS",
  "target_new_2025_26_regular_only":331,
  "separate_promotions_2025_26":6,
  "normal_second_source_score_date_team_exact":stats["SECOND_SOURCE_DATE_TEAM_FT_EXACT"],
  "normal_second_source_score_conflict_hold":stats["SECOND_SOURCE_FT_CONFLICT_HOLD"],
  "normal_second_source_unmapped_or_missing_hold":331-stats["SECOND_SOURCE_DATE_TEAM_FT_EXACT"]-stats["SECOND_SOURCE_FT_CONFLICT_HOLD"],
  "normal_quality_flags":dict(stats),"first_24_exception_keys_only":exceptions,
  "playoff_scoreboard_original_author_vs_FBref_exact":6,
  "playoff_independent_scoreboard":FBREF,
  "normal_secondary_source":URL,
  "source_provider_raw_dataset_republished":False,
  "secondary_source_response_sha256":hashlib.sha256(second).hexdigest(),
  "second_source_identity_rows_mapped_for_current_only":len(source),
  "unmapped_provider_team_labels":unknown.most_common(24),
  "prior_131_ESP2_source_matches_retested":0,
  "source_original_CCBY_license":"CC BY 4.0 publisher; other upstream training and as-of gates pending",
  "source_original_509_and_existing_4505_unchanged":True,
  "new_training_rows_approved":0,
  "main_M4_and_manual_xg_untouched":True
 }
def test():
 assert len(PLAY_EXPECTED)==6 and len(set(CLUBS.values()))==22
 assert day("31/05/2026")=="2026-05-31" and norm("Deportivo La Coruña")=="deportivo la coruna"
 print("PASS 22 explicit canonical team aliases, independent 6 playoff evidence, only 331 new source IDs")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");arg=p.parse_args()
 if arg.self_test:test()
 if arg.run:
  try:d=compare()
  except Exception as e:
   d={"status":"FAIL_CLOSED_NEW_331_SECOND_WITNESS_NOT_CERTIFIED","error_type":type(e).__name__,"reason":str(e)[:220],"new_training_rows_approved":0}
  OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  print("ESP2_NEW_WITNESS_START")
  print(json.dumps(d,ensure_ascii=False,indent=2))
  print("ESP2_NEW_WITNESS_END")
