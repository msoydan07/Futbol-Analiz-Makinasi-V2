"""User-approved 20 Nov 2026 templates, read-only PDF PRESENTATION only.

Morning: league-scoped 6-card white/black/red PDF; second review: symmetrical
4-box single fixture PDF. No model selection, new seals, odds fetch, lineup
assertions, percentage edits, or use of odds to change a morning decision.
"""
from __future__ import annotations
import math
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

BLACK=HexColor("#161616")
RED=HexColor("#cf1524")
BORDER=HexColor("#bdbdbd")
GRAY=HexColor("#555555")
W,H=A4
LEFT=35
RIGHT=W-35
CW=RIGHT-LEFT
FONT="ApprovedArimo"
BOLD="ApprovedArimoBold"
LABELS={"MS1":"MS 1","MSX":"MS X","MS2":"MS 2",
        "OVER_2.5":"2.5 ÜST","UNDER_2.5":"2.5 ALT",
        "BTTS_YES":"KG VAR","BTTS_NO":"KG YOK"}
GROUP={"MS1":"MS","MSX":"MS","MS2":"MS",
       "OVER_2.5":"GOALS_2.5","UNDER_2.5":"GOALS_2.5",
       "BTTS_YES":"KG","BTTS_NO":"KG"}
LEAGUES={"ENG1":"PREMIER LEAGUE","ENG2":"CHAMPIONSHIP",
"GER1":"BUNDESLIGA","ESP1":"LA LIGA","ITA1":"SERIE A",
"FRA1":"LIGUE 1","NED1":"EREDIVISIE","TUR1":"TÜRKİYE SÜPER LİG",
"POR1":"PRIMEIRA LIGA","BEL1":"PRO LEAGUE"}
MONTHS=("","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz",
        "Ağustos","Eylül","Ekim","Kasım","Aralık")
WEEKDAYS=("PAZARTESİ","SALI","ÇARŞAMBA","PERŞEMBE","CUMA","CUMARTESİ","PAZAR")


def _fonts():
    if FONT in pdfmetrics.getRegisteredFontNames():return
    candidates=(
       ("/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf",
        "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"),
       ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
       ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    for normal,bold in candidates:
        if Path(normal).is_file() and Path(bold).is_file():
            pdfmetrics.registerFont(TTFont(FONT,normal))
            pdfmetrics.registerFont(TTFont(BOLD,bold))
            return
    raise ValueError("APPROVED_UNICODE_ARIAL_LIKE_FONT_NOT_AVAILABLE")

def _text(c,x,y,value,size=9,bold=False,color=BLACK,max_width=None):
    txt=str(value or "—").replace("\n"," ").replace("\r"," ")
    font=BOLD if bold else FONT
    if max_width is not None and pdfmetrics.stringWidth(txt,font,size)>max_width:
        while txt and pdfmetrics.stringWidth(txt+"…",font,size)>max_width:
            txt=txt[:-1]
        txt+="…"
    c.setFont(font,size);c.setFillColor(color);c.drawString(x,y,txt)

def _right(c,x,y,value,size=9,bold=False,color=BLACK,max_width=None):
    txt=str(value or "—").replace("\n"," ").replace("\r"," ")
    font=BOLD if bold else FONT
    if max_width is not None and pdfmetrics.stringWidth(txt,font,size)>max_width:
        while txt and pdfmetrics.stringWidth(txt+"…",font,size)>max_width:
            txt=txt[:-1]
        txt+="…"
    c.setFont(font,size);c.setFillColor(color);c.drawRightString(x,y,txt)

def _center(c,x,y,value,size=9,bold=False,color=BLACK):
    c.setFont(BOLD if bold else FONT,size)
    c.setFillColor(color);c.drawCentredString(x,y,str(value or "—"))

def _box(c,x,y,width,height):
    c.setFillColor(HexColor("#ffffff"));c.setStrokeColor(BORDER)
    c.setLineWidth(.7);c.roundRect(x,y,width,height,10,fill=1,stroke=1)

def _p(v):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not 0<=v<=1:
        return "—"
    return ("%.1f%%"%(100*v)).replace(".",",")

def _o(v):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<=1:
        return "—"
    return ("%.2f"%v).replace(".",",")

def _delta(v):
    if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v):
        return "—"
    return ("%+.1f"%(v)).replace(".",",")

def _date(v):
    try:
        d=date.fromisoformat(v)
        return str(d.day)+" "+MONTHS[d.month]+" "+str(d.year)
    except (ValueError,TypeError):
        return str(v or "—")

def _fair(row,market):
    group=(row.get("market_no_vig") or {}).get(GROUP.get(market),{})
    if group.get("status")!="FULL_MARKET_QUOTE_AVAILABLE":return None
    return (group.get("no_vig") or {}).get(market)

def _valid_decision(row,session):
    d=row.get("model_first_decision")
    if not isinstance(d,dict):return None
    from model_first_decision_263 import verified,SCHEMA,REF_SCHEMA
    verified(d,SCHEMA)
    if (d.get("forecast_sha256")!=row.get("model_forecast_sha256")
        or d.get("baseline_sha256")!=row.get("empirical_baseline_sha256")
        or d.get("model_policy_sha256")!=session.get("policy_dev_lock_sha256")
        or d.get("price_used_in_decision") is not False):
        raise ValueError("APPROVED_PDF_DECISION_SHA_LINK_INVALID")
    reference=row.get("market_fifth_reference")
    if not isinstance(reference,dict):raise ValueError("APPROVED_PDF_REFERENCE_MISSING")
    verified(reference,REF_SCHEMA)
    if (reference.get("decision_sha256")!=d["payload_sha256"] or
        reference.get("source_pdf_sha256")!=session.get("pdf_sha256") or
        reference.get("odds_used_for_model_selection") is not False):
        raise ValueError("APPROVED_PDF_ODDS_SOURCE_LINK_INVALID")
    return d

def _extract_card(row,session):
    """Fixed v3 3-column display; each engine's highest event is INDEPENDENT.

    Model-first decision is SHA-verified by the existing stage. P2 sidecar is
    generated from first iddaa PDF AFTER the model decision and carried in the
    signed morning session. It cannot steer or override model selection.
    """
    d=_valid_decision(row,session)
    main=d.get("main_candidate") if d else None
    alt=d.get("alternative_candidate") if d else None
    model_market=main.get("market") if isinstance(main,dict) else None
    p2=row.get("p2_agreement")
    p0_market=None;p0_prob=None;p2_status="ORAN EKSİK";p2_gap=None
    if d and isinstance(p2,dict):
        if p2.get("model_decision_sha256")!=d.get("payload_sha256"):
            raise ValueError("REPORT_P2_DIFFERENT_FROZEN_MODEL_SHA")
        if p2.get("forecast_sha256") not in (None,row.get("model_forecast_sha256")):
            raise ValueError("REPORT_P2_WRONG_FORECAST_SHA")
        snap=row.get("pdf_first_price_snapshot") or {}
        if (p2.get("source",{}).get("snapshot_sha256")
            and p2["source"]["snapshot_sha256"]!=snap.get("payload_sha256")):
            raise ValueError("REPORT_P2_DIFFERENT_PDF_PRICE_SHA")
        if p2.get("p0_highest_is_global") is True:
            p0_market=p2.get("p0_highest_choice")
            p0_prob=p2.get("p0_highest_probability")
            if p0_market not in LABELS or not isinstance(p0_prob,(int,float)):
                raise ValueError("REPORT_P0_LEADER_INVALID")
            p2_status={"UYUMLU":"UYUMLU",
                       "TERCIHLER_FARKLI":"FARKLI",
                       "YUZDELER_UZAK":"YÜZDELER UZAK"}.get(p2.get("status"),"—")
            if p2_status=="—":raise ValueError("REPORT_P2_UNKNOWN_STATUS")
            if p2_status=="UYUMLU" or p2_status=="YÜZDELER UZAK":
                p2_gap=p2.get("absolute_gap_pp")
                if not isinstance(p2_gap,(int,float)) or p2_gap<0:
                    raise ValueError("REPORT_P2_INVALID_GAP")
        else:
            p2_status="ORAN EKSİK"
    if not d:p2_status="TEKNİK ENGEL"
    if d and not main:p2_status="MODEL PAS"
    ours=main.get("calibrated_probability") if main else None
    return {
        "home":row.get("pdf_home") or "?",
        "away":row.get("pdf_away") or "?",
        "league":row.get("league") or "?",
        "date":row.get("match_date_tr"),"time":row.get("kickoff_time_tr") or "—",
        "main":LABELS[model_market] if main else "MODEL PAS" if d else "TEKNİK ENGEL",
        "ours":_p(ours),
        "p0":LABELS.get(p0_market,"—"),
        "p0_pct":_p(p0_prob),
        "p2_status":p2_status,
        "p0_odds":_o((row.get("prices") or {}).get(p0_market)) if p0_market else "—",
        "p2_gap":(("%.2f"%p2_gap).replace(".",",")+" puan"
                  if p2_gap is not None else "—"),
        # Original compatibility fields used by model-only SHA gate.
        "fair":_p(p0_prob),
        "diff":_delta(p2_gap) if p2_gap is not None else "—",
        "alternative":(LABELS[alt["market"]]+" "+_p(alt.get("calibrated_probability"))
                       if alt else "YOK"),
        "main_odds":_o((row.get("prices") or {}).get(model_market)) if model_market else "—",
        "forecast_sha":row.get("model_forecast_sha256"),
        "decision_sha":d.get("payload_sha256") if d else None,
    }

def render_batch(session,target):
    """Render no invented selection: only verified, signed decision and user PDF odds."""
    from iddaa_pdf_session_263 import SCHEMA
    from iddaa_pdf_first_quote_263 import sha256
    if session.get("schema")!=SCHEMA:raise ValueError("APPROVED_BATCH_SCHEMA_INVALID")
    if ("signed_research_session_sha256" in session and
        session["signed_research_session_sha256"]!=sha256(
          {k:v for k,v in session.items() if k!="signed_research_session_sha256"})):
        raise ValueError("APPROVED_BATCH_SHA_INVALID")
    target=Path(target)
    if target.exists():raise FileExistsError("APPROVED_BATCH_PDF_NEVER_OVERWRITE")
    _fonts()
    rows=[_extract_card(row,session) for row in session.get("rows",[])
          if row.get("status")!="SKIPPED_OUT_OF_10_LEAGUES"]
    grouped={}
    for r in rows:grouped.setdefault((r["league"],r["date"]),[]).append(r)
    return _draw_grouped_cards(grouped,target)


def _draw_grouped_cards(grouped,target,model_only=False):
    """Permanent mobile three-column first-PDF layout, maximum six cards/page.

    Exactly: ANA MAKİNE | P0 | P2: UYUMLU/FARKLI/ORAN EKSİK.
    P2 underneath: original iddaa price, then same-event percentage-point gap.
    No public 'Şart 1/2' labels, no price-driven change to main decision.
    This same geometry is also used by price-free NEW100 reports.
    """
    _fonts()
    c=canvas.Canvas(str(target),pagesize=A4,pageCompression=1)
    c.setTitle("2.6.3 - Üç Makine Sabah Toplu Analiz v3")
    pages=0
    for (league,day),games in grouped.items():
        for start in range(0,len(games),6):
            chunk=games[start:start+6];pages+=1
            _text(c,LEFT,H-49,LEAGUES.get(league,league),18.5,True)
            try: weekday=WEEKDAYS[date.fromisoformat(day).weekday()]
            except (ValueError,TypeError): weekday="TARİH DOĞRULANAMADI"
            _text(c,LEFT,H-69,_date(day).upper()+"  ·  "+weekday+"  ·  "+str(len(games))+" MAÇ",8.4,True)
            _right(c,RIGHT,H-53,"SABAH / MODEL-ONLY" if model_only
                   else "SABAH / İLK İDDAA PDF",8,True)
            _text(c,LEFT,H-94,"MS 1-X-2   /   2.5 ALT-ÜST   /   KG VAR-YOK",8.1)
            for i,r in enumerate(chunk):
                top=H-113-i*107;bottom=top-104
                _box(c,LEFT,bottom,CW,104)
                _box(c,LEFT+10,top-29,55,19)
                _text(c,LEFT+17,top-23,r.get("time","—"),8.2,True)
                _text(c,LEFT+72,top-22,
                    str(r.get("home","?"))+" - "+str(r.get("away","?")),9.6,True,
                    max_width=CW-141)
                _right(c,RIGHT-12,top-22,
                       str(start+i+1).zfill(2)+"/"+str(len(games)).zfill(2),8.0,True)
                c.setStrokeColor(BORDER);c.setLineWidth(.45)
                c.line(LEFT+12,top-34,RIGHT-12,top-34)
                col_w=(CW-28)/3
                xx=(LEFT+13,LEFT+13+col_w,LEFT+13+2*col_w)
                for col in (1,2):
                    x=LEFT+12+col*col_w
                    c.line(x,top-39,x,top-88)
                _text(c,xx[0]+5,top-46,"ANA MAKİNE",7.6,True)
                _text(c,xx[0]+5,top-64,r.get("main","TEKNİK ENGEL"),12.3,True,
                      max_width=col_w-12)
                _text(c,xx[0]+5,top-81,r.get("ours","—"),12.1,True)
                _text(c,xx[1]+8,top-46,"P0",7.6,True)
                _text(c,xx[1]+8,top-64,r.get("p0","—"),12.3,True,max_width=col_w-16)
                _text(c,xx[1]+8,top-81,r.get("p0_pct","—"),12.1,True)
                _text(c,xx[2]+8,top-46,"P2: "+str(r.get("p2_status") or
                      ("ORAN EKSİK" if model_only else "—")),
                      8.0,True,max_width=col_w-14)
                _text(c,xx[2]+8,top-64,"Oran: "+str(r.get("p0_odds","—")),9,True)
                _text(c,xx[2]+8,top-82,"Fark: "+str(r.get("p2_gap","—")),
                      8.9,True,RED,max_width=col_w-14)
                _text(c,LEFT+15,top-97,"Alternatif: "+str(r.get("alternative","YOK")),
                      8.2,True,RED,max_width=CW-30)
            footer=H-113-len(chunk)*107-5
            _text(c,LEFT,footer,
                  "ANA ve P0 kendi en yüksek tercihlerini bağımsız seçer; P2 sadece karşılaştırır.",7.2)
            _text(c,LEFT,footer-15,
                  "Oran: ilk iddaa PDF'sindeki P0 lideri. Fark: yalnız aynı tercihse yüzde puanı.",7.2)
            _text(c,LEFT,footer-29,
                  "Eksik fiyat uydurulmaz. Mühürlü model kararı ve alternatif değiştirilmez.",7.2)
            c.showPage()
    if not pages:
        _text(c,LEFT,H-60,"TOPLU ANALİZ",18,True)
        _text(c,LEFT,H-88,"Gönderilen PDF'de kapsamdaki 10 ligden maç bulunmadı.",10)
        c.showPage()
    c.save()
    return target

def render_model_only_batch(day,rows,target):
    """Reuse the identical approved cards for SHA-linked NEW100 without odds.

    Callers MUST provide the approved_card payload derived from an actual
    original forecast and verified same-SHA model-first decision.
    No fictitious bookmaker quotes, market %, odds or effect on selection.
    """
    target=Path(target)
    if target.exists():raise FileExistsError("APPROVED_BATCH_PDF_NEVER_OVERWRITE")
    grouped={}
    for row in rows:
        card=row.get("approved_card")
        if not isinstance(card,dict):raise ValueError("MODEL_ONLY_CARD_NOT_SHA_VERIFIED")
        if (not card.get("forecast_sha") or not card.get("decision_sha") or
            card.get("fair")!="VERİ YOK" or card.get("diff")!="—" or
            card.get("main_odds")!="—"):
            raise ValueError("MODEL_ONLY_CARD_INVALID_OR_FORGED_PRICE")
        if card.get("date")!=day or card.get("league")!=row.get("league"):
            raise ValueError("MODEL_ONLY_CARD_DATE_LEAGUE_MISMATCH")
        grouped.setdefault((card["league"],day),[]).append(card)
    return _draw_grouped_cards(grouped,target,model_only=True)

def _lines(s, max_width, size, max_lines):
    words=str(s).split();out=[];line=""
    for word in words:
        candidate=(line+" "+word).strip()
        if line and pdfmetrics.stringWidth(candidate,FONT,size)>max_width:
            out.append(line);line=word
        else:line=candidate
    if line:out.append(line)
    if len(out)>max_lines:
        raise ValueError("COMMENTARY_EXCEEDS_ONE_PAGE_SOURCE_FACTS_NEED_SECOND_PAGE")
    return out

def _row_odds(d,markets):
    vals=[d.get(k) for k in markets]
    return " / ".join(_o(x) for x in vals)

def _single_commentary(r,market,old,new):
    name=LABELS.get(market,"ana tercih")
    parts=["Sabahki "+name+" tercihi ve model yüzdesi korunuyor."]
    if isinstance(old,(int,float)) and isinstance(new,(int,float)):
        move=new-old
        if abs(move)<.015:
            parts.append("İlk ve son iddaa oranları arasında belirgin bir değişim görülmedi.")
        else:
            direction="yükseldi" if move>0 else "düştü"
            parts.append("Ana pazar oranı "+_o(old)+"'den "+_o(new)+"'ye "+direction+".")
            parts.append("Bu hareket piyasanın ilgili sonuca yaklaşımındaki değişimi gösteriyor; kesin nedeni yalnız oranlardan çıkarılamaz.")
    else:parts.append("Ana pazarın ilk ve son oranı birlikte doğrulanamadı; oran hareketi yorumu yapılamıyor.")
    xi=r.get("lineups") or {}
    facts=xi.get("comments") or []
    if facts:
        parts.append("İlk 11 için aktarılan kaynaklı gözlemlerde "+
                     "; ".join(str(t.get("fact","")).rstrip(".")+" ("+
                               str(t.get("football_reason","")).rstrip(".")+")"
                               for t in facts[:2])+".")
        parts.append("Bu bilgiler kod tarafından bağımsız doğrulanmadı; oran hareketinin bunlardan kaynaklandığı kesin söylenemez.")
    else:
        parts.append("İlk 11 veya kadro değişimi hakkında karşılaştırılabilir kaynaklı futbol gelişmesi bulunmadığından bu yönde neden uydurulmadı.")
    parts.append("İkinci kontrol yeni tahmin veya ikinci mühür oluşturmadı.")
    return " ".join(parts)

def _draw_approved_single_page(c,r,i,n):
    """Draw the ONLY approved second-PDF A4 four-symmetric-box layout."""
    # User-approved symmetrical four-box layout on A4.
    for y,height in ((H-135,104),(H-304,154),(H-529,209),(H-758,214)):
        _box(c,LEFT,y,CW,height)
    def section(y,label):
        _text(c,LEFT+17,y,label,10.5,True)
        c.setStrokeColor(BORDER);c.setLineWidth(.45)
        c.line(LEFT+17,y-11,RIGHT-17,y-11)
    section(H-54,"MAÇ BİLGİSİ")
    _text(c,LEFT+17,H-85,r.get("home","?")+" - "+r.get("away","?"),14,True,max_width=CW-35)
    _text(c,LEFT+17,H-105,LEAGUES.get(r.get("league"),"LİG")+
          "  •  "+_date(r.get("match_date_tr")),8.7)
    _right(c,RIGHT-17,H-105,"Saat: "+str(r.get("kickoff_time_tr") or "—"),9,True)
    section(H-169,"ANA TAHMİN")
    main=r.get("morning_main_choice") or {}
    alt=r.get("morning_alternative_choice") or {}
    market=main.get("market")
    ours=main.get("calibrated_probability")
    firstfair=(r.get("morning_market_no_vig") or {}).get(GROUP.get(market),{})
    latefair=(r.get("latest_market_no_vig") or {}).get(GROUP.get(market),{})
    f0=((firstfair.get("no_vig") or {}).get(market)
        if firstfair.get("status")=="FULL_MARKET_QUOTE_AVAILABLE" else None)
    f1=((latefair.get("no_vig") or {}).get(market)
        if latefair.get("status")=="FULL_MARKET_QUOTE_AVAILABLE" else None)
    if not isinstance(ours,(int,float)) or isinstance(ours,bool) or not 0<=ours<=1:ours=None
    diff=100*(ours-f0) if ours is not None and isinstance(f0,(int,float)) else None
    xs=[LEFT+66,LEFT+196,LEFT+324,LEFT+447]
    headings=["ANA TERCİH","BİZİM %","PİYASA %","FARK"]
    values=[LABELS.get(market,"TEKNİK ENGEL"),_p(ours),_p(f0),_delta(diff)+" puan" if diff is not None else "—"]
    for idx,(x,h,v) in enumerate(zip(xs,headings,values)):
        _center(c,x,H-199,h,8,True,RED if idx==3 else BLACK)
        _center(c,x,H-226,v,12.5,True,RED if idx==3 else BLACK)
    for x in (LEFT+130,LEFT+260,LEFT+385):
        c.setStrokeColor(BORDER);c.setLineWidth(.35)
        c.line(x,H-236,x,H-189)
    alttext=(LABELS[alt["market"]]+" "+_p(alt.get("calibrated_probability"))
             if alt and alt.get("market") in LABELS else "YOK")
    _text(c,LEFT+18,H-266,"Alternatif: "+alttext,9,True,RED,max_width=CW-35)
    _text(c,LEFT+18,H-282,"Sabahki tahmin, model olasılığı ve SHA mührü değişmez.",7.5,color=GRAY)
    section(H-323,"ORAN KARŞILAŞTIRMASI")
    odds0=r.get("morning_odds") or {};odds1=r.get("latest_odds") or {}
    main0=odds0.get(market);main1=odds1.get(market)
    x0=LEFT+17;split=LEFT+360
    _text(c,x0,H-352,"PAZAR",7.5,True)
    _text(c,LEFT+138,H-352,"İLK ORAN",7.5,True)
    _text(c,LEFT+245,H-352,"SON ORAN",7.5,True)
    groups=(("MS 1 / X / 2",("MS1","MSX","MS2")),
           ("2.5 ALT / ÜST",("UNDER_2.5","OVER_2.5")),
           ("KG VAR / YOK",("BTTS_YES","BTTS_NO")))
    for j,(name,marks) in enumerate(groups):
        yy=H-386-j*33
        _text(c,x0,yy,name,8,True)
        _text(c,LEFT+135,yy,_row_odds(odds0,marks),8,max_width=98)
        _text(c,LEFT+240,yy,_row_odds(odds1,marks),8,max_width=105)
        c.setStrokeColor(BORDER);c.line(x0,yy-15,split-12,yy-15)
    c.setStrokeColor(BORDER);c.line(split,H-346,split,H-516)
    _text(c,split+14,H-362,"ANA ORAN",8,True)
    _text(c,split+14,H-386,_o(main0)+"  →  "+_o(main1),10,True)
    odiff=main1-main0 if isinstance(main1,(float,int)) and isinstance(main0,(float,int)) else None
    _text(c,split+14,H-422,"ORAN FARKI",8,True,RED)
    _text(c,split+14,H-444,("%+.2f"%odiff).replace(".",",") if odiff is not None else "—",11,True,RED)
    newdiff=100*(ours-f1) if ours is not None and isinstance(f1,(float,int)) else None
    _text(c,split+14,H-480,"YENİ FARK",8,True,RED)
    _text(c,split+14,H-501,(_delta(newdiff)+" puan") if newdiff is not None else "—",11,True,RED)
    section(H-548,"YORUM")
    commentary=_single_commentary(r,market,main0,main1)
    comment_lines=_lines(commentary,CW-36,9.6,12)
    yy=H-578
    for line in comment_lines:
        _text(c,LEFT+18,yy,line,9.6);yy-=15.5
    _text(c,LEFT,H-775,"Kaynak: 1. ve 2. kullanıcı iddaa PDF'si. Kadro bilgisi varsa kaynaklı iddia, otomatik teyit değil.",7.4,color=GRAY,max_width=CW)
    _text(c,LEFT,H-790,"Bu bir ikinci tahmin değildir. Oranlar ilk sabah kararını değiştirmez.",7.4,color=GRAY)
    _right(c,RIGHT,21,str(i+1)+"/"+str(n),8.3,True)
    c.showPage()

def render_singles(review,target_dir,bundle_pdf=None):
    """Approved singles plus optional canonical one-page-per-fixture bundle."""
    if review.get("schema")!="263_SINGLE_MORNING_SEAL_ONE_PREKO_REVIEW_V1":
        raise ValueError("APPROVED_SINGLE_REVIEW_SCHEMA_INVALID")
    _fonts();base=Path(target_dir)
    if base.exists():raise FileExistsError("APPROVED_SINGLE_DIRECTORY_ALREADY_EXISTS")
    ready=[r for r in review.get("rows",[]) if r.get("status")==
           "GUNCEL_ORAN_KAYDI_VE_KADRO_DURUMU_HAZIR"]
    if not ready:
        raise ValueError("NO_VERIFIED_SECOND_PDF_PREKICKOFF_MATCH_FOR_SINGLE_REPORT")
    bundle=Path(bundle_pdf) if bundle_pdf is not None else None
    if bundle is not None and bundle.exists():
        raise FileExistsError("APPROVED_SINGLE_BUNDLE_ALREADY_EXISTS")
    base.mkdir(parents=True,exist_ok=False)
    combined=(canvas.Canvas(str(bundle),pagesize=A4,pageCompression=1)
              if bundle is not None else None)
    if combined is not None:
        combined.setTitle("2.6.3 - Onaylı İkinci PDF Tekli Maç Raporları")
    made=[]
    for i,r in enumerate(ready):
        target=base/("tekli_"+str(i+1).zfill(2)+".pdf")
        c=canvas.Canvas(str(target),pagesize=A4,pageCompression=1)
        c.setTitle("2.6.3 - Onaylı Tekli Maç İnceleme")
        _draw_approved_single_page(c,r,i,len(ready))
        c.save();made.append(target)
        if combined is not None:
            _draw_approved_single_page(combined,r,i,len(ready))
    if combined is not None:
        combined.save()
    return made
