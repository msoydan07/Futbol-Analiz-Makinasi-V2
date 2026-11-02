"""Attach four read-only model predictions and no-vig benchmark to 2.6.3 report."""
from market_benchmark_263 import compare,render,GROUPS,MARKETS

def make_reference(models,quotes,fixture,now):
    if not isinstance(quotes,dict):raise ValueError("QUOTE_INPUT_NOT_A_MAP")
    key=":".join((fixture["league"],fixture["home_id"],fixture["away_id"],fixture["local_date"]))
    available={}
    for name in ("MS","KG","GOALS_1.5","GOALS_2.5","GOALS_3.5"):
        members=GROUPS[name]
        present=[quotes[k] for k in members if k in quotes]
        if not present:continue
        first=present[0]
        if any(x!=first for x in present[1:]):
            raise ValueError("MIXED_ODDS_SNAPSHOTS_IN_SAME_GROUP")
        available[name]=compare(models=models,quote=first,fixture_key=key,
                                kickoff=fixture["kickoff_utc"],now=now.isoformat())
    return {"schema":"263_readonly_quad_market_report_v1",
            "models":models,
            "reference_status":"NO_LIVE_ODDS_ADAPTER" if not available else "SYNCHRONIZED_QUOTE_INPUT_CONDITIONAL",
            "benchmarks":available,
            "market_reference_not_main_model_selection":True,
            "model_promotions":[],"approved_A_B_C":[],
            "pilot_recorded":False,"production_modified":False}

def render_four_report(result):
    lines=["## Dört modelin ayrı çıktıları ve piyasa referansı",
           "**Salt-okunur; tahmin kaydı, ana model terfisi veya resmî A/B/C yoktur.**",
           "| Model | MS 1 | MS X | MS 2 | 2.5 Üst | KG Var |",
           "|---|---:|---:|---:|---:|---:|"]
    for name in ("B","C2","C3","M4"):
        record=result["models"][name]
        if record["status"]!="AVAILABLE":
            lines.append("| "+name+" | — | — | — | — | — |")
            continue
        p=record["goals"]["markets"]
        ms=p["1X2"] if "1X2" in p else {"H":p["MS1"],"D":p["MSX"],"A":p["MS2"]}
        pct=lambda n: format(n*100,".1f")+"%"
        lines.append("| "+name+" | "+pct(ms["H"])+" | "+pct(ms["D"])+" | "+
                     pct(ms["A"])+" | "+pct(p["OVER_2.5"])+" | "+pct(p["BTTS_YES"])+" |")
    if not result["benchmarks"]:
        lines+=["","Piyasa karşılaştırması: **DOĞRULANAMADI** — analiz anında bağımsız kontrol edilmiş tam karşı oranlar henüz yok."]
    else:
        for group,benchmark in result["benchmarks"].items():
            lines+=["",render(benchmark)]
    lines+=["","Piyasaya yakın olmak, daha doğru tahmin demek değildir. Sonuç bazlı kabul daha sonra.",
            "C2 kanonik referans olarak korunur; modellerin ortalaması alınmaz."]
    return "\n".join(lines)
