#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Karar Hakemi V1: read-only three-expert decision for new or research matches.

Usage for six already verified historical joins:
  python HAKEM_KARAR_UYGULA_V1.py --rule <hakem_karar_kurali_v1.json> \
      --input <M4_HAFIZA_6_MAC_KARSILASTIRMA_KAYDI_20261123.json> --output ./decisions.json
For future, provide a JSON with `matches:[{match,expert_probabilities:{
   M4_C3_V4:{MS1,...}, P0:{MS1,...}, HAFIZA:{MS1,...}
}}]` with all seven probabilities for each expert. Must supply independently
verified same-fixture identity and first-PDF odds; the tool does not prove either.
Does not use score or final match result to select the event. Does not promise
profitability or independently calibrated probability.
"""
from __future__ import annotations
import argparse,json,math,hashlib
from pathlib import Path
EVENTS=('MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO')
FAMILIES={'MS':('MS1','MSX','MS2'),'OU25':('OVER_2.5','UNDER_2.5'),'KG':('BTTS_YES','BTTS_NO')}
NAMES={'MS1':'MS 1','MSX':'MS X','MS2':'MS 2','OVER_2.5':'2.5 Üst','UNDER_2.5':'2.5 Alt','BTTS_YES':'KG Var','BTTS_NO':'KG Yok'}
SOURCES=('M4_C3_V4','P0','HAFIZA')

def validate(v):
 if not isinstance(v,dict) or set(v)!=set(EVENTS):raise ValueError('YEDI_OLASILIK_EKSIK_YA_DA_FAZLA')
 try:p={k:float(v[k]) for k in EVENTS}
 except Exception as e:raise ValueError('SAYISAL_OLASILIK_GEREKLI') from e
 if any(not math.isfinite(x) or not 0<=x<=1 for x in p.values()):raise ValueError('OLASILIK_ARALIGI_GECERSIZ')
 for fs in FAMILIES.values():
  if abs(sum(p[k] for k in fs)-1)>2e-5:raise ValueError('PAZAR_TOPLAMI_BIR_OLMALI')
 return p

def load_weights(path):
 doc=json.loads(Path(path).read_text(encoding='utf-8'))
 if doc.get('schema')!='HAKEM_RETROSPECTIVE_THREE_EXPERT_REBUILD_V1':raise ValueError('TRAIN_CONFIG_SCHEMA_MISMATCH')
 d=doc.get('teacher_family_weights')
 if not isinstance(d,dict) or set(d)!=set(FAMILIES):raise ValueError('FAMILY_WEIGHTS_MISSING')
 w={f:[float(v) for v in d[f]] for f in FAMILIES}
 for f in FAMILIES:
  if len(w[f])!=3 or any(not math.isfinite(x) or x<0 for x in w[f]) or abs(sum(w[f])-1)>1e-6:
   raise ValueError('FAMILY_WEIGHT_INVALID_'+f)
 return w,doc

def choose(experts,weights):
 if not isinstance(experts,dict) or set(experts)!=set(SOURCES):raise ValueError('THREE_EXPERTS_REQUIRED')
 values={s:validate(experts[s]) for s in SOURCES}
 joined={}
 for family,keys in FAMILIES.items():
  for key in keys:
   joined[key]=sum(weights[family][i]*values[source][key] for i,source in enumerate(SOURCES))
 ordered=sorted(EVENTS,key=lambda k:(-joined[k],EVENTS.index(k)))
 main=ordered[0];fam=next(f for f,ks in FAMILIES.items() if main in ks)
 alternative=next(k for k in ordered[1:] if k not in FAMILIES[fam])
 return {'ana_tercih':main,'ana_tercih_tr':NAMES[main],
         'hakem_arastirma_yuzdesi':round(joined[main]*100,2),
         'alternatif_tercih':alternative,'alternatif_tr':NAMES[alternative],
         'alternatif_yuzdesi':round(joined[alternative]*100,2),
         'tum_7_hakem_yuzdeleri':{k:round(joined[k]*100,2) for k in EVENTS},
         'ana_tercih_uzman_yuzdeleri':{s:round(values[s][main]*100,2) for s in SOURCES},
         'model_surum':'HAKEM_V1_HISTORICAL_SHRUNK_WEIGHTS',
         'guven_durumu':'GECMISE_DAYALI_ARASTIRMA_KARARI_GARANTI_YOK'}

def apply(doc,weights):
 if not isinstance(doc.get('records',doc.get('matches')),list):raise ValueError('MATCHES_OR_RECORDS_MISSING')
 items=doc.get('records',doc.get('matches'))
 if not items or len(items)>100:raise ValueError('MATCH_COUNT_1_TO_100')
 result=[]
 for x in items:
  if 'expert_probabilities' in x:
   experts=x['expert_probabilities'];label=x.get('mobile_match_name',x.get('match',''))
  else:
   experts=x.get('experts');label=x.get('match','')
  if not isinstance(label,str) or not label:raise ValueError('MATCH_LABEL_REQUIRED')
  result.append({'match':label,'league':x.get('league'),'match_date':x.get('local_match_date',x.get('date')),
                 **choose(experts,weights)})
 return {'schema':'HAKEM_DECISION_OUTPUT_V1','status':'RESEARCH_PREMATCH_OR_RETROSPECTIVE_DEPENDS_ON_INPUT_SOURCE',
         'data_from':'USER_M4_P0_HAFIZA_THREE_VECTORS','count':len(result),'decisions':result,
         'warning':'Hakem yüzdeleri tarihsel ağırlıklı bileşimdir; gerçek kazanma ihtimalinin bağımsız doğrulaması değildir. Geçmiş maçları yeni mühür gösterme.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--rule',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();weights,_=load_weights(a.rule)
 data=json.loads(a.input.read_text(encoding='utf-8'))
 out=apply(data,weights);a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'count':out['count'],'decisions':[{k:v for k,v in x.items() if k in ('match','ana_tercih_tr','hakem_arastirma_yuzdesi','alternatif_tr','alternatif_yuzdesi')} for x in out['decisions']]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
