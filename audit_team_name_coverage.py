"""Audit 10-league team-name resolution in one report, no guesses or ID edits."""
import csv,json
from collections import Counter
from pathlib import Path
from identity import Registry
from team_name_resolver import resolve

def run(registry_path="data/match_registry.json",memberships_path="data/team_memberships.csv",aliases_path="data/team_aliases_reviewed.csv"):
 registry=Registry(registry_path)
 with open(memberships_path,encoding="utf-8-sig",newline="") as f:memberships=list(csv.DictReader(f))
 rows=[];seen=set()
 for member in memberships:
  league=member["league"];team_id=member["team_id"]
  if (league,team_id) in seen:continue
  seen.add((league,team_id))
  name=registry.data["teams"][team_id]["name"]
  try:
   resolved=resolve(registry,league,name,aliases_path)
   status="MATCHED" if resolved==team_id else "CONFLICT"
  except KeyError:status="UNMATCHED"
  rows.append({"league":league,"team_id":team_id,"registry_name":name,"status":status})
 counts=dict(Counter(row["status"] for row in rows))
 result={"registry_teams":len(registry.data["teams"]),"league_memberships":len(rows),
         "coverage":counts,"mackolik_names_verified":False,
         "note":"Checks internal identity resolution only; external Maçkolik names require independently collected evidence."}
 Path("data/team_name_coverage_audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 with open("data/team_name_coverage_audit.csv","w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=["league","team_id","registry_name","status"]);w.writeheader();w.writerows(rows)
 print(json.dumps(result,ensure_ascii=False))
 if counts.get("CONFLICT",0) or counts.get("UNMATCHED",0):raise SystemExit("Team identity coverage audit failed")
 return result
if __name__=="__main__":run()
