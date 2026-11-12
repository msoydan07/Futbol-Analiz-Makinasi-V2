"""Read-only error-driven parser context, no odds or model forecasting."""
import json,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from ten_league_source_probe_263 import SOURCES
from official_page_lookup_263 import _Markup,_default_fetch
from iddaa_pdf_team_alias_preflight_263 import index_registry,resolve_label
from official_page_lookup_263 import parse_official_events

def one(league):
  url,parser=SOURCES[league]
  try:
    _,html=_default_fetch(url,league)
    p=_Markup();p.feed(html)
    raw=re.sub(r"\s+"," ","".join(p.visible))
    patterns={
      "ENG2":["21-Nov-26","Millwall","Queens Park Rangers","Championship"],
      "ITA1":["21 nov 2026","Como","Cagliari","Giornata 12"],
      "FRA1":["11e JOURNÉE","Vendredi 20 novembre","ESTAC Troyes"],
      "TUR1":["21.11.2026","GALATASARAY A.Ş.","12.Hafta"],
      "POR1":["Jornada 12","Sexta-feira, 27 de novembro","Marítimo M."],
      "NED1":["zaterdag 21 november","N.E.C."],
      "BEL1":["21 nov","KV Mechelen"]
    }[league]
    parts=[]
    for key in patterns:
      m=re.search(re.escape(key),raw,re.I)
      if m:
        parts.append({"key":key,"found":True,"visible_window":raw[max(0,m.start()-110):min(len(raw),m.start()+410)]})
      else:parts.append({"key":key,"found":False})
    rows=[row for row in p.rows if any(key.casefold() in " ".join(row).casefold() for key in patterns)]
    out={"league":league,"bytes":len(html),"row_samples":rows[:3],"row_count":len(p.rows),
         "windows":parts}
    if league in ("ENG2","ITA1","POR1"):
      needles={
        "ENG2":["21-Nov-26","Millwall","Championship","Sky Sports"],
        "ITA1":["Como","Cagliari","Giornata 12","2026-11-21","MATCHDAY 12"],
        "POR1":["Jornada 12","Jornada 11","Marítimo","Mar\\u00edtimo","27 de novembro",
                "FC Porto","Sporting CP","Horários definidos até à 12.ª jornada"]
      }[league]
      out["raw_evidence"]=[]
      for needle in needles:
        at=html.casefold().find(needle.casefold())
        out["raw_evidence"].append({"needle":needle,"present":at>=0,
            "window":html[max(0,at-85):at+230] if at>=0 else ""})
    if league=="NED1":
      index,_,_=index_registry()
      events=parse_official_events("NED1",html,"knvb")
      out["unmapped"]=[{"home":m["home"],"away":m["away"],
               "home_status":resolve_label("NED1",m["home"],index)["status"],
               "away_status":resolve_label("NED1",m["away"],index)["status"]}
        for m in events if "2026-11-20"<=m["match_date"]<="2026-11-30"
        and (resolve_label("NED1",m["home"],index)["status"]!="MAPPED"
         or resolve_label("NED1",m["away"],index)["status"]!="MAPPED")]
    return out
  except Exception as e:
    return {"league":league,"status":"FETCH_BLOCKED","exception":type(e).__name__,
            "detail":str(e)[:80]}
def main():
  with ThreadPoolExecutor(max_workers=7) as pool:
    futures={pool.submit(one,l):l for l in ("ENG2","ITA1","FRA1","TUR1","POR1","NED1","BEL1")}
    for f in as_completed(futures):
      print("LIVE_263_CONTEXT="+json.dumps(f.result(),ensure_ascii=False)[:4500],flush=True)
if __name__=="__main__":main()
