"""Read-only, user-approved MONOCHROME MOBILE PDF + single-match PDF from sealed new100.

Uses the same SHA-validated morning batch and verified same-time Pinnacle
comparison; never fetches a quote, reruns a model, changes PAS or a forecast.
No displayed decimal odds. PDF is presentation, not an immutable pilot entry.
The black/white boxed design is the permanent user-approved default.
"""
from __future__ import annotations
import argparse,math,statistics,json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from sabah_mobile_screens_263 import load_row,decision,ScreenError
from sabah_pinnacle_new100_bridge_263 import render as price_render
from sabah_batch_263 import SCHEMA,sha
from classification_odds_263 import canonical_markets
from forward_c3 import read_aware
from zoneinfo import ZoneInfo

SCHEMA_PDF="263_APPROVED_COMPACT_MOBILE_PDF_V1"  # stable output schema
MARKETS=("BTTS_YES","OVER_1.5","OVER_2.5","OVER_3.5")
MARKET_LABELS=("KG Var","1,5 Ust","2,5 Ust","3,5 Ust")
MODELS=("B","C2","C3","M4")
DIRECTIONS=(("MS1","MS 1"),("MSX","MS X"),("MS2","MS 2"))
TR=ZoneInfo("Europe/Istanbul")
W,H=420,690
# User-approved monochrome boxed result display, 2026-11-08.
# Keep report/match SHA verification, prices, markets and pilot selection untouched.
INK=HexColor("#111111");TEAL=HexColor("#111111")
MUTED=HexColor("#555555");PALE=HexColor("#f2f2f2")
EDGE=HexColor("#bdbdbd");WHITE=HexColor("#ffffff")
CARD_ALT=HexColor("#fafafa");CHIP=HexColor("#ededed")
MONOCHROME_APPROVED_V2=True
FONT_REG="MobileDejaVu";FONT_BOLD="MobileDejaVuBold"
class MobileBlocked(ValueError):pass

def fonts():
    for label,filename in ((FONT_REG,"DejaVuSans.ttf"),(FONT_BOLD,"DejaVuSans-Bold.ttf")):
        if label not in pdfmetrics.getRegisteredFontNames():
            path=Path("/usr/share/fonts/truetype/dejavu")/filename
            if not path.is_file():raise MobileBlocked("REQUIRED_PDF_FONT_UNAVAILABLE")
            pdfmetrics.registerFont(TTFont(label,str(path)))

def number(p):
    if isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1:
        return None
    return float(p)

def pct(p):
    n=number(p)
    return ("%.1f"%(n*100)).replace(".",",")+"%" if n is not None else "—"

def difference(n):
    if not isinstance(n,(float,int)) or isinstance(n,bool) or not math.isfinite(n):return "—"
    return ("%+.1f"%n).replace(".",",")

def cut(txt,max_width,font=FONT_BOLD,size=10):
    txt=str(txt).replace("\n"," ").replace("|","/")
    if pdfmetrics.stringWidth(txt,font,size)<=max_width:return txt
    while txt and pdfmetrics.stringWidth(txt+"…",font,size)>max_width:
        txt=txt[:-1]
    return txt+"…"

def row_data(report,price,root):
    if report.get("schema")!=SCHEMA or report.get("cohort")!="new100":
        raise MobileBlocked("NOT_NEW100_BATCH")
    if report.get("payload_sha256")!=sha({k:v for k,v in report.items() if k!="payload_sha256"}):
        raise MobileBlocked("MORNING_SHA_CHANGED")
    if price.get("day_turkey")!=report.get("day_turkey") or price.get("cohort")!="new100":
        raise MobileBlocked("PRICE_DAY_OR_COHORT_MISMATCH")
    price_rows={p["forecast_path"]:p for p in price["items"]}
    if len(price_rows)!=len(price["items"]):raise MobileBlocked("DUPLICATE_PRICE_FORECAST")
    matched=set();rows=[]
    for r in report["outcomes"]:
        if r.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
        if r["forecast_path"] not in price_rows:raise MobileBlocked("MISSING_PRICE_MATCH")
        f=load_row(root,r);p=price_rows[r["forecast_path"]]
        if p["forecast_sha256"]!=f["payload_sha256"]:
            raise MobileBlocked("PRICE_FORECAST_SHA_WRONG")
        if p.get("status")=="READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED":
            if p.get("original_PAS_decision_sha256")!=r.get("decision_sha256"):
                raise MobileBlocked("PRICE_DECISION_SHA_WRONG")
        d=decision(root,"new100",report["day_turkey"],Path(r["forecast_path"]).stem,f)
        diagnostic={x["market"]:x for x in (d or {}).get("all_market_diagnostics",[])
                    if isinstance(x,dict) and "market" in x}
        cal=[(m,label,number(diagnostic.get(m,{}).get("calibrated_probability")))
             for m,label in DIRECTIONS]
        cal=[x for x in cal if x[2] is not None]
        choice=max(cal,key=lambda x:x[2]) if cal else (None,"MS —",None)
        side=choice[0]
        fair=None
        if p.get("status")=="READ_ONLY_SAME_TIME_PINNACLE_AND_CALIBRATED" and side:
            q=p.get("calibrated_MS_research",{}).get(side,{})
            if q.get("status")=="DESCRIPTIVE_CALIBRATED_PINNACLE_RESEARCH" and number(q.get("calibrated_probability")) is not None:
                if abs(q["calibrated_probability"]-choice[2])>1e-9:
                    raise MobileBlocked("MARKET_AND_MODEL_CALIBRATION_DISAGREE")
                fair=number(q.get("pinnacle_no_vig"))
        median=[]
        for market in MARKETS:
            vals=[]
            for name in MODELS:
                m=f["model_predictions"].get(name,{})
                if m.get("status")!="AVAILABLE":continue
                try:
                    z=canonical_markets(m["goals"]["markets"])
                    x=number(z.get(market))
                except (ValueError,TypeError,KeyError):
                    continue
                if x is not None:vals.append(x)
            median.append(statistics.median(vals) if vals else None)
        kickoff=read_aware(f["fixture"]["kickoff_utc"]).astimezone(TR)
        rows.append(dict(time=kickoff.strftime("%H:%M"),league=f["fixture"]["league"],
                         home=r["home"],away=r["away"],direction=choice[1],
                         model=choice[2],market=fair,
                         delta=(100*(choice[2]-fair)) if fair is not None and choice[2] is not None else None,
                         goals=median,models=f["model_predictions"],
                         forecast_sha=f["payload_sha256"],
                         decision_sha=d["payload_sha256"] if d else None,
                         locked_at=f["created_at_utc"],
                         source=f["fixture"].get("official_source"),
                         quote_status=p.get("status"),
                         status="PAS / ONAYSIZ",
                         id=Path(r["forecast_path"]).stem))
        matched.add(r["forecast_path"])
    if set(price_rows)!=matched:raise MobileBlocked("ORPHAN_PRICE_ROW")
    return rows

def text(c,x,y,value,size=9,bold=False,color=INK):
    c.setFont(FONT_BOLD if bold else FONT_REG,size)
    c.setFillColor(color);c.drawString(x,y,str(value))

def right(c,x,y,value,size=9,bold=False,color=INK):
    c.setFont(FONT_BOLD if bold else FONT_REG,size)
    c.setFillColor(color);c.drawRightString(x,y,str(value))

def header(c,day,title):
    c.setFillColor(TEAL);c.rect(0,H-9,W,9,stroke=0,fill=1)
    text(c,13,H-31,title,14,True,TEAL)
    text(c,13,H-47,day+" | TSİ | 2.6.3",8,False,MUTED)

def foot(c,page,extra=""):
    c.setStrokeColor(EDGE);c.line(13,27,W-13,27)
    text(c,13,15,"MS: kalibre | KG/Ust: model medyani | Fiyat yoksa piyasa —",6.2,color=MUTED)
    right(c,W-13,15,str(page),7,color=MUTED)

def match(c,r,y,i):
    """Stable high-contrast monochrome card; visual changes only, no new choices."""
    shade=CARD_ALT if i%2 else WHITE
    c.setFillColor(shade)
    c.setStrokeColor(EDGE)
    c.setLineWidth(.65)
    c.roundRect(10,y-45,W-20,57,6,stroke=1,fill=1)
    text(c,17,y,r["time"],8.3,True,INK)
    match_name=cut(r["home"]+" – "+r["away"],178,FONT_BOLD,9.2)
    text(c,57,y,match_name,9.2,True,INK)
    right(c,W-17,y,r["direction"],8.4,True,INK)
    text(c,57,y-13,r["league"],7,color=MUTED)
    text(c,123,y-13,"BIZIM",6.5,color=MUTED)
    text(c,208,y-13,"PIYASA",6.5,color=MUTED)
    text(c,307,y-13,"FARK (yp)",6.5,color=MUTED)
    text(c,123,y-26,pct(r["model"]),9.4,True,INK)
    text(c,208,y-26,pct(r["market"]),9.4,True,INK)
    text(c,307,y-26,difference(r["delta"]),9.4,True,INK)
    for z,(label,p) in enumerate(zip(MARKET_LABELS,r["goals"])):
        x=15+z*98
        c.setFillColor(CHIP)
        c.setStrokeColor(EDGE)
        c.setLineWidth(.35)
        c.roundRect(x,y-43,94,12,3,stroke=1,fill=1)
        text(c,x+3,y-40,label+": "+pct(p),6.6,True,INK)

def batch_pdf(path,day,rows):
    fonts();p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(p),pagesize=(W,H),pageCompression=1,invariant=1)
    n=0;y=H-74
    for i,r in enumerate(rows):
        if y<100:
            foot(c,n);c.showPage();y=H-74
        if y==H-74:
            n+=1;header(c,day,"44 mac degil: bugunun onayli mobil tablosu")
        match(c,r,y,i);y-=66
    if not rows:
        n=1;header(c,day,"Mobil mac analizi")
        text(c,15,H-100,"Muhurlenmis yeni mac bulunamadi.",11,True)
    foot(c,n);c.save()
    return p

def single_pdf(path,day,r):
    fonts();p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(p),pagesize=(W,H),pageCompression=1,invariant=1)
    header(c,day,"TEKLI MAC ANALIZI")
    text(c,13,H-76,cut(r["home"]+" – "+r["away"],W-28,FONT_BOLD,14),14,True)
    text(c,13,H-92,r["league"]+" | "+r["time"]+" TSİ | "+r["direction"],9,color=MUTED)
    for x,label,value in ((13,"BIZIM",pct(r["model"])),(150,"PIYASA",pct(r["market"])),(290,"FARK (yp)",difference(r["delta"]))):
        text(c,x,H-125,label,8,color=MUTED);text(c,x,H-146,value,15,True,TEAL)
    text(c,13,H-175,"GOL BEKLENTILERI (model medyani)",9,True)
    for j,(name,pct_value) in enumerate(zip(MARKET_LABELS,r["goals"])):
        x=13+j*101
        c.setFillColor(PALE);c.setStrokeColor(EDGE);c.setLineWidth(.6);c.roundRect(x,H-221,94,35,5,stroke=1,fill=1)
        text(c,x+5,H-198,name,7,color=MUTED)
        text(c,x+5,H-213,pct(pct_value),11,True)
    text(c,13,H-250,"DORT MODEL KARSILASTIRMASI",10,True)
    ys=H-272
    text(c,18,ys,"MODEL",8,True);text(c,112,ys,"MS 1",8,True)
    text(c,180,ys,"MS X",8,True);text(c,248,ys,"MS 2",8,True)
    text(c,316,ys,"KG VAR",8,True)
    for j,name in enumerate(MODELS):
        m=r["models"].get(name,{})
        vals={}
        if m.get("status")=="AVAILABLE":
            try:vals=canonical_markets(m["goals"]["markets"])
            except (KeyError,ValueError,TypeError):pass
        yy=ys-24-j*25
        c.setFillColor(PALE if j%2==0 else WHITE)
        c.rect(12,yy-6,W-24,23,stroke=0,fill=1)
        text(c,18,yy,name,8,True)
        for x,k in ((112,"MS1"),(180,"MSX"),(248,"MS2"),(316,"BTTS_YES")):
            text(c,x,yy,pct(vals.get(k)),8)
    y=ys-145
    text(c,13,y,"ANA TERCIH: PAS / RESMI ONAY YOK",9,True)
    text(c,13,y-19,"Alternatif: YOK | Piyasa verisi yoksa fark gosterilmez.",8,color=MUTED)
    text(c,13,y-39,"KAYIT VE KANIT",9,True)
    text(c,13,y-57,"Tahmin SHA: "+r["forecast_sha"],7)
    text(c,13,y-72,"Karar SHA: "+str(r["decision_sha"] or "YOK"),7)
    text(c,13,y-87,"Tahmin UTC: "+r["locked_at"],7)
    text(c,13,y-102,"Piyasa: "+cut(r["quote_status"],320,FONT_REG,7),7)
    text(c,13,y-117,"Resmi fikstur: "+cut(r["source"] or "KANIT YOK",340,FONT_REG,7),7)
    foot(c,1);c.save()
    return p

def run(report,receipt,price,root,day,out):
    """Regenerate price comparison and assert identity, then only render PDF."""
    from sabah_pinnacle_new100_bridge_263 import read as read_json
    report=read_json(report);receipt=read_json(receipt)
    price_saved=read_json(price)
    regenerated=price_render(report,receipt,root,Path(root)/"experiments/263/pinnacle_daily_snapshots")
    if price_saved!=regenerated:raise MobileBlocked("PRICE_REPORT_NOT_REPRODUCIBLE")
    if day!=report["day_turkey"]:raise MobileBlocked("WRONG_DAY")
    rows=row_data(report,price_saved,root)
    target=Path(out);target.mkdir(parents=True,exist_ok=True)
    batch_pdf(target/"toplu.pdf",day,rows)
    single_dir=target/"tekli";single_dir.mkdir(exist_ok=True)
    for row in rows:single_pdf(single_dir/(row["id"]+".pdf"),day,row)
    return len(rows)

def main():
    p=argparse.ArgumentParser()
    for a in ("report","receipt","price","day","out"):p.add_argument("--"+a,required=True)
    p.add_argument("--root",default=".")
    a=p.parse_args()
    count=run(a.report,a.receipt,a.price,a.root,a.day,a.out)
    print(json.dumps({"schema":SCHEMA_PDF,"batch_pdf":str(Path(a.out)/"toplu.pdf"),
                      "single_pdfs":count,"betting_authorized":False,"no_new_api_calls":True}))
if __name__=="__main__":main()
