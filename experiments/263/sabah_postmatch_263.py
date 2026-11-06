"""Read-only scoring of SHA-sealed forward forecasts; no retroactive registration."""
import hashlib,json,math
from collections import defaultdict
MODELS=('B','C2','C3','M4');KEYS=('H','D','A')
def canonical(x):
 return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def sealed(x,schema):
 if x.get('schema')!=schema:raise ValueError('SCHEMA_MISMATCH')
 if hashlib.sha256(canonical({k:v for k,v in x.items() if k!='payload_sha256'})).hexdigest()!=x.get('payload_sha256'):raise ValueError('SHA_MISMATCH')
def probabilities(p):
 if not isinstance(p,dict) or set(p)!=set(KEYS):raise ValueError('INVALID_1X2_KEYS')
 if any(isinstance(p[k],bool) or not isinstance(p[k],(int,float)) or not math.isfinite(p[k]) or not 0<=p[k]<=1 for k in KEYS) or abs(sum(p.values())-1)>1e-4:raise ValueError('INVALID_1X2')
 return p
def scores(p,outcome):
 probabilities(p)
 if outcome not in KEYS:raise ValueError('INVALID_RESULT')
 return {'brier':sum((p[k]-(k==outcome))**2 for k in KEYS),'log_loss':-math.log(max(p[outcome],1e-15)),'correct_direction':max(KEYS,key=lambda k:p[k])==outcome}
def evaluate(rows):
 per=defaultdict(list);common=[];seen=set();blocked=[]
 for row in rows:
  f=row['forecast'];sealed(f,'quad_forward_263_v1');sha=f['payload_sha256']
  if sha in seen:raise ValueError('DUPLICATE_FORECAST')
  seen.add(sha);outcome=row.get('official_result')
  if outcome not in KEYS or row.get('result_verified') is not True:
   blocked.append({'forecast_sha256':sha,'reason':'RESULT_NOT_VERIFIED'});continue
  ps={}
  for model in MODELS:
   m=f.get('model_predictions',{}).get(model,{})
   if m.get('status')=='AVAILABLE':
    try:ps[model]=probabilities(m['goals']['markets']['1X2'])
    except (KeyError,ValueError,TypeError):pass
  market=row.get('pinnacle')
  if market is not None:
   sealed(market,'263_pinnacle_readonly_benchmark_v1')
   if market.get('status')=='READ_ONLY_SAME_TIME_BENCHMARK' and market.get('forecast_sha256')==sha and market.get('bookmaker')=='pinnacle':
    ps['Pinnacle']=probabilities(market['pinnacle_no_vig_probabilities'])
  for source,p in ps.items():per[source].append(scores(p,outcome))
  if all(k in ps for k in (*MODELS,'Pinnacle')):common.append({k:scores(ps[k],outcome) for k in (*MODELS,'Pinnacle')})
 def agg(items):
  n=len(items)
  return {'n':n,'brier':sum(x['brier'] for x in items)/n if n else None,'log_loss':sum(x['log_loss'] for x in items)/n if n else None,'direction_accuracy':sum(x['correct_direction'] for x in items)/n if n else None}
 return {'schema':'POSTMATCH_SCORE_V1','sealed_forecasts_seen':len(seen),'verified_results':len(seen)-len(blocked),'blocked':blocked,'all_eligible':{k:agg(per[k]) for k in (*MODELS,'Pinnacle')},'common_five_source_n':len(common),'common_five_source':{k:agg([x[k] for x in common]) for k in (*MODELS,'Pinnacle')},'forecast_modified':False,'pinnacle_is_not_fifth_football_model':True}
