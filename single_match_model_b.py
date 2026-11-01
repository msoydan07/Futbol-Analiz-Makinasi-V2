"""Single-match experimental analysis adapter; requires independently verified fixture IDs."""
import argparse,csv,json,math
from datetime import date
from pathlib import Path
from experimental_poisson_baseline import estimate,poisson

def analyze(rows,league,home,away,day):
 date.fromisoformat(day)
 if home==away:raise ValueError("Home and away must differ")
 p=estimate(rows,league,home,away,day)
 report={"version":"single_match_model_b_v1_experimental","fixture":{"league":league,"home_id":home,"away_id":away,"date":day},"status":"READY" if p else "INSUFFICIENT_HISTORY","data_cutoff_exclusive":day,"source":"data/historical_results.csv","fixture_verified":False,"lineup_status":"NOT_CHECKED_NOT_BLOCKING","odds_status":"NOT_COLLECTED","ev_status":"NOT_CALCULATED","limitations":["Fixture must be verified independently","No lineup, injury, current form beyond recorded goals, odds, corners or first-half projections","Model B experimental, not a betting recommendation"]}
 if not p:return report
 mass=p["matrix_mass"]
 if not (0.999<=mass<=1.000001):raise ValueError("Poisson matrix tail exceeds 0.1 percent; reject probabilities")
 h,a=p["lambda_home"],p["lambda_away"]
 scores=[{"score":str(i)+"-"+str(j),"probability":poisson(h,i)*poisson(a,j)/mass} for i in range(11) for j in range(11)]
 scores.sort(key=lambda x:x["probability"],reverse=True)
 z=sum(p[k] for k in ("p_home","p_draw","p_away"))
 report["model"]={"method":p["method"],"expected_goals":{"home":h,"away":a},"history_samples":{"league":p["league_samples"],"home":p["home_samples"],"away":p["away_samples"]},"markets":{"1x2":{"home":p["p_home"]/z,"draw":p["p_draw"]/z,"away":p["p_away"]/z},"over_2_5":p["p_over25"]/mass,"under_2_5":1-p["p_over25"]/mass,"btts_yes":p["p_btts"]/mass,"btts_no":1-p["p_btts"]/mass},"top_scores":scores[:5],"tail_mass":p["tail_mass"]}
 return report

def main():
 parser=argparse.ArgumentParser()
 for key in ("league","home-id","away-id","date"):parser.add_argument("--"+key,required=True)
 parser.add_argument("--output",default="data/single_match_model_b.json")
 args=parser.parse_args()
 with Path("data/historical_results.csv").open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 report=analyze(rows,args.league,args.home_id,args.away_id,args.date)
 path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"fixture":report["fixture"],"output":str(path)}))
if __name__=="__main__":main()
