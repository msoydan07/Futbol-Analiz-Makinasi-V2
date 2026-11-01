"""Offline smoke checks for single-match adapter, no external data needed."""
from single_match_model_b import analyze
def run():
 rows=[]
 for i in range(40):
  rows.append({"fixture_id":str(i),"league":"TEST","match_date":"2025-01-%02d"%(i%28+1),"home_id":"A" if i%2==0 else "B","away_id":"B" if i%2==0 else "A","home_goals":"2","away_goals":"1","result":"H"})
 p=analyze(rows,"TEST","A","B","2025-02-01")
 assert p["status"]=="READY",p
 m=p["model"]["markets"]
 assert abs(sum(m["1x2"].values())-1)<1e-10
 assert abs(m["over_2_5"]+m["under_2_5"]-1)<1e-10
 assert abs(m["btts_yes"]+m["btts_no"]-1)<1e-10
 assert p["fixture_verified"] is False
 assert analyze(rows,"TEST","A","B","2024-01-01")["status"]=="INSUFFICIENT_HISTORY"
 print("single_match_smoke_pass")
if __name__=="__main__":run()
