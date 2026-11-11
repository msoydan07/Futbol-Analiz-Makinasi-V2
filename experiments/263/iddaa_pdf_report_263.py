"""Compact black-white, mobile-readable PDF report for a 263 iddaa PDF-first session.

Only MS1/X/2, 2.5 Alt/Üst, KG Var/Yok. No 1.5 or 3.5.
Presents raw model percentages and snapshot no-vig; these are diagnostics,
NOT calibrated betting-edge proofs. Main/alternative remain PAS unless an
independent validated policy record explicitly allows their display.
"""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
from iddaa_pdf_session_263 import SCHEMA,PDF_TO_MARKET,MARKET_GROUPS

ROWS=(
 ("MS 1","MS1","MS"),("MS X","MSX","MS"),("MS 2","MS2","MS"),
 ("2.5 Alt","UNDER_2.5","GOALS_2.5"),
 ("2.5 Üst","OVER_2.5","GOALS_2.5"),
 ("KG Var","BTTS_YES","KG"),("KG Yok","BTTS_NO","KG"),
)
CANONICAL_MARKETS=frozenset(x[1] for x in ROWS)

def _font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular=(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    bold=(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
    normal=next((p for p in regular if Path(p).is_file()),None)
    strong=next((p for p in bold if Path(p).is_file()),None)
    if not normal or not strong:
        raise RuntimeError("PDF_UNICODE_FONT_NOT_AVAILABLE")
    pdfmetrics.registerFont(TTFont("IddaaReport",normal))
    pdfmetrics.registerFont(TTFont("IddaaReportBold",strong))
    return "IddaaReport","IddaaReportBold"

def _pct(value):
    return "—" if value is None else f"%{100*value:.1f}".replace(".",",")

def _odds(value):
    return "—" if value is None else f"{value:.2f}".replace(".",",")

def _pp(value):
    return "—" if value is None else f"{value:+.1f}".replace(".",",")

def _render_pick(row,session):
    """Accept a pick only from a frozen decision carrying the SAME PDF SHA.

    Current 2.6.3 calibration policy does not yet supply this PDF-first
    binding. Until there is a linked SHA-pinned decision: PAS, never guess.
    """
    d=row.get("pdf_linked_policy_decision")
    if not isinstance(d,dict):
        return "ANA: —     ALTERNATİF: —     DURUM: PAS (kalibre karar yok)"
    if (d.get("pdf_sha256")!=session["pdf_sha256"] or
        d.get("forecast_sha256")!=row.get("model_forecast_sha256") or
        d.get("frozen_policy_verified") is not True):
        return "ANA: —     ALTERNATİF: —     DURUM: PAS (karar kanıtı eşleşmedi)"
    market=d.get("main_market")
    alternate=d.get("alternative_market")
    if market is not None and market not in CANONICAL_MARKETS:
        return "ANA: —     ALTERNATİF: —     DURUM: PAS (yasak pazar)"
    if alternate is not None and alternate not in CANONICAL_MARKETS:
        return "ANA: —     ALTERNATİF: —     DURUM: PAS (yasak alternatif)"
    pretty={k:label for label,k,_ in ROWS}
    return ("ANA: "+pretty.get(market,"—")+
            "     ALTERNATİF: "+pretty.get(alternate,"—")+
            "     DURUM: KOŞULLU ARAŞTIRMA (bahis onayı değil)")

def _table_for(row,norm,bold,font):
    from reportlab.platypus import Table,TableStyle,Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    textstyle=ParagraphStyle("tab",fontName=font,fontSize=8.0,leading=10.5)
    centered=ParagraphStyle("cent",parent=textstyle,alignment=1)
    cols=[
      ["Pazar","İddaa oran","M4 ham %","Piyasa %","Fark (yp)"]
    ]
    prices=row.get("prices") or {}
    market_fairs=row.get("market_no_vig") or {}
    models=row.get("model_1x2_and_core_markets") or {}
    m4=models.get("M4",{})
    for label,market,grp in ROWS:
        market_data=market_fairs.get(grp,{})
        fair=(market_data.get("no_vig") or {}).get(market)
        p=m4.get(market)
        if not isinstance(p,(int,float)) or isinstance(p,bool):p=None
        edge=100*(p-fair) if p is not None and fair is not None else None
        cols.append([label,_odds(prices.get(market)),_pct(p),
                     _pct(fair),_pp(edge)])
    widths=[120,96,93,100,85]
    tabl=Table(cols,colWidths=widths,repeatRows=1,
               hAlign="LEFT",rowHeights=[24]+[21]*7)
    tabl.setStyle(TableStyle([
      ("FONTNAME",(0,0),(-1,0),bold),
      ("FONTNAME",(0,1),(-1,-1),font),
      ("FONTSIZE",(0,0),(-1,-1),8),
      ("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),
      ("GRID",(0,0),(-1,-1),0.5,colors.black),
      ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
      ("ALIGN",(1,1),(-1,-1),"CENTER"),
      ("LEFTPADDING",(0,0),(-1,-1),8),
      ("TOPPADDING",(0,0),(-1,-1),4),
      ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    return tabl

def build(session,output):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    if session.get("schema")!=SCHEMA:
        raise ValueError("SESSION_SCHEMA_INVALID")
    target=Path(output)
    if target.exists():raise FileExistsError("REPORT_NEVER_OVERWRITE")
    font,bold=_font()
    page_w,page_h=A4
    fmt=lambda size,name=font,lead=None:ParagraphStyle(
        "p"+str(size)+name,fontName=name,fontSize=size,
        leading=lead or size*1.4,textColor=colors.black,alignment=TA_LEFT,
        spaceAfter=0)
    title=fmt(13,bold)
    subtitle=fmt(8)
    matchstyle=fmt(10,bold)
    small=fmt(7.8)
    story=[
      Paragraph("FUTBOL MAÇ ANALİZ MAKİNASI 2.6.3 — ORANLI RAPOR",title),
      Spacer(1,8),
      Paragraph("Kaynak: Kullanıcı İddaa PDF'si · Alınış: "+
                str(session.get("pdf_capture_utc"))+" · "+
                "Maç sayısı: "+str(session.get("n_rows")),subtitle),
      Paragraph("PDF SHA256: "+str(session.get("pdf_sha256",""))[:32]+"…",small),
      Paragraph("Kapsam: MS 1/X/2 · 2.5 Alt/Üst · KG Var/Yok | "+
                "Karşı fiyatlar: aynı PDF | Başka bahis pazarları yok",subtitle),
      Spacer(1,16)
    ]
    for row in session["rows"]:
        if row.get("status")=="SKIPPED_OUT_OF_10_LEAGUES":
            continue
        number=int(row.get("index",0))+1
        home=str(row.get("pdf_home") or "?")
        away=str(row.get("pdf_away") or "?")
        # HTML escape for arbitrary team names from user-supplied PDF
        from xml.sax.saxutils import escape
        headline=(f"{number:02d} · {escape(home)} — {escape(away)}")
        meta=(f"{escape(str(row.get('league') or 'Lig belirsiz'))}"
              f"  |  {escape(str(row.get('match_date_tr') or '—'))}"
              f"  {escape(str(row.get('kickoff_time_tr') or '—'))}"
              f"  |  Durum: {escape(str(row.get('status') or '—'))}")
        segments=[Paragraph(headline,matchstyle),Spacer(1,4),
                  Paragraph(meta,small),Spacer(1,7),
                  _table_for(row,None,bold,font),
                  Spacer(1,9),
                  Paragraph(escape(_render_pick(row,session)),small)]
        if row.get("model_1x2_and_core_markets"):
            modelbits=[]
            for m in ("B","C2","C3","M4"):
                p=row["model_1x2_and_core_markets"].get(m,{})
                if all(k in p for k in ("MS1","OVER_2.5","BTTS_YES")):
                    modelbits.append(f"{m}: MS1 {_pct(p['MS1'])}, "
                                     f"2.5 Üst {_pct(p['OVER_2.5'])}, "
                                     f"KG Var {_pct(p['BTTS_YES'])}")
                else:
                    modelbits.append(f"{m}: veri yok")
            segments+=[Spacer(1,6),Paragraph(
                escape("  |  ".join(modelbits)),small)]
        segments+=[Spacer(1,5),Paragraph(
            "Fark = M4 ham % − piyasa marjsız %. Pozitif fark tek başına "
            "kalibre bahis avantajı değildir.",small),Spacer(1,20)]
        story.append(KeepTogether(segments))
    if not any(r.get("status")!="SKIPPED_OUT_OF_10_LEAGUES"
               for r in session["rows"]):
        story.append(Paragraph("Kapsamdaki 10 ligden maç bulunmadı.",subtitle))
    def footer(canvas,doc):
        canvas.saveState()
        canvas.setFont(font,7)
        canvas.drawString(36,25,"2.6.3 · İddaa PDF ilk kaynak · Araştırma raporu")
        canvas.drawRightString(page_w-36,25,"Sayfa "+str(doc.page))
        canvas.restoreState()
    doc=SimpleDocTemplate(str(target),pagesize=A4,
         leftMargin=36,rightMargin=36,topMargin=34,bottomMargin=44,
         title="Futbol 2.6.3 — Oranlı İddaa PDF Raporu")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--session-json",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    source=json.loads(Path(args.session_json).read_text(encoding="utf-8"))
    print(str(build(source,args.out)))

if __name__=="__main__":main()
