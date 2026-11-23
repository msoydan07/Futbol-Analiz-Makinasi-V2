#!/usr/bin/env python3
# coding: utf-8
"""Read-only iddaa-PDF geometric odds extraction + explicitly labelled theoretical imputation.

No offered odds are fabricated. The original PDF layout must have a handicap-column
anchor for each match; individual market slots are mapped by x position, never by
shifting the next quote into the missing slot.  Imputation uses a *measured* median
bookmaker overround from complete market families in the supplied PDF. If that
cannot be estimated, the market remains partial; the rest of the match can run.
"""
from __future__ import annotations
import hashlib, math, re, statistics
from pathlib import Path

KEYS=('MS1','MSX','MS2','OVER_2.5','UNDER_2.5','BTTS_YES','BTTS_NO')
FAMILIES={'MS':KEYS[:3],'OU25':KEYS[3:5],'KG':KEYS[5:7]}
PDF_SLOTS={'MS1':0,'MSX':1,'MS2':2,'UNDER_2.5':9,'OVER_2.5':10,'BTTS_YES':11,'BTTS_NO':12}
REVERSE_PDF={v:k for k,v in PDF_SLOTS.items()}
class OddsAuditError(ValueError):pass

def _is_odds(s):return bool(re.fullmatch(r'\d{1,3}[.,]\d{2,3}',str(s)))

def _safe_odd(s):
    v=float(str(s).replace(',','.'))
    if not math.isfinite(v) or not 1.0<v<=1000.0:raise OddsAuditError('INVALID_BOOKMAKER_QUOTE')
    return v

def _rows_from_page(page):
    """For iddaa 13-column printable bulletin; no fuzzy match-name substitution."""
    words=page.get_text('words')
    blocks=[b for b in page.get_text('blocks') if isinstance(b[4],str)]
    out=[]
    for w in words:
        if not re.fullmatch(r'[0-2]\d:[0-5]\d',w[4]) or not 90<=w[0]<=160:continue
        time=w[4]; y=w[1]
        block_candidates=[b[4] for b in blocks if b[1]-4<=y<=b[3]+4 and re.search(r'\b'+re.escape(time)+r'\b',b[4])]
        match=None
        for block in block_candidates:
            mm=re.search(re.escape(time)+r'\s*\n([^\n]{3,130}[-–—][^\n]{2,130})\s*\n\+',block)
            if mm:match=mm.group(1).strip();break
        if not match:continue
        current=[z for z in words if abs(z[1]-y)<=3.1 and 180<z[0]<470]
        hd=[z for z in current if re.fullmatch(r'\d{1,2}:\d{1,2}',z[4])]
        if len(hd)!=1:
            out.append({'time':time,'match':match,'error':'NO_UNIQUE_HANDICAP_COLUMN_ANCHOR',
                        'raw':{k:None for k in KEYS}});continue
        anchor=hd[0][0]
        candidates=[z for z in current if _is_odds(z[4])]
        expected=[anchor-91+15*j for j in range(6)]+[anchor+13+15*j for j in range(7)]
        matched={};unassigned=[]
        for z in candidates:
            distances=[abs(z[0]-xx) for xx in expected]
            ix=min(range(13),key=lambda j:distances[j])
            # Position tolerance chosen to permit normal variable-width printed odds,
            # but not adjacent-cell reassignment (cell pitch ~15 pt).
            if distances[ix]>6.0 or ix in matched:unassigned.append(z[4]);continue
            matched[ix]=_safe_odd(z[4])
        if unassigned:
            out.append({'time':time,'match':match,
                        'error':'AMBIGUOUS_PDF_ODDS_GEOMETRY:'+','.join(unassigned),
                        'raw':{k:None for k in KEYS}});continue
        raw={k:matched.get(PDF_SLOTS[k]) for k in KEYS}
        out.append({'time':time,'match':match,'raw':raw,'observed_slots':len(matched),
                    'missing_keys':[k for k in KEYS if raw[k] is None],
                    'pdf_layout':'IDDAA_13_COL_POSITION_ANCHORED'})
    return out

def read_iddaa_pdf(source):
    try:import fitz
    except ImportError as e:raise OddsAuditError('PYMUPDF_REQUIRED') from e
    raw=source if isinstance(source,bytes) else Path(source).read_bytes()
    doc=fitz.open(stream=raw,filetype='pdf')
    rows=[]
    for p in doc:rows.extend(_rows_from_page(p))
    if not rows:raise OddsAuditError('NO_VERIFIABLE_IDDAA_ROWS_FOUND')
    seen=set()
    for r in rows:
        key=(r['time'],r['match'])
        if key in seen:raise OddsAuditError('DUPLICATE_PDF_FIXTURE_LABEL_AND_TIME')
        seen.add(key)
    return {'status':'IDDAA_GEOMETRIC_SOURCE',
            'pdf_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows}

def _family_margin(quotes,keys):
    if not all(quotes.get(k) is not None for k in keys):return None
    margin=sum(1/float(quotes[k]) for k in keys)-1
    if not -.015<=margin<=.55:return None
    return margin

def measure_margins(rows):
    vals={f:[] for f in FAMILIES}
    for row in rows:
        for f,ks in FAMILIES.items():
            m=_family_margin(row['raw'],ks)
            if m is not None:vals[f].append(m)
    return vals

def _choose_margin(family,all_margins):
    own=all_margins[family]
    if own:return statistics.median(own),f'SAME_FAMILY_COMPLETE_MARKETS_N_{len(own)}',own
    same_size=[m for f,ms in all_margins.items() if len(FAMILIES[f])==len(FAMILIES[family]) and f!=family for m in ms]
    if same_size:return statistics.median(same_size),f'OTHER_SAME_SIZE_FAMILY_N_{len(same_size)}',same_size
    any_markets=[m for ms in all_margins.values() for m in ms]
    if any_markets:return statistics.median(any_markets),'OTHER_MARKET_TYPE_BORROWED_WEAK',any_markets
    return None,'OVERROUND_NOT_OBSERVABLE',[]

def complete_quote_rows(rows):
    """Fill ONLY exactly one absent quote within a family, with provenance + range.

    Under/overround is not uniquely recoverable from observed quotes alone;
    median is an inference from independent *complete* families in this PDF.
    All partial/missing-market states remain visible; no data source masquerades
    as genuine quoted odds.
    """
    margins=measure_margins(rows);output=[]
    for original in rows:
        r={**original,'real_odds':dict(original['raw']),'effective_odds':dict(original['raw']),
           'estimated_quotes':{},'unresolved_markets':[],'market_status':{}}
        if r.get('error'):
            r['market_status']={f:'READER_UNVERIFIED' for f in FAMILIES}
            output.append(r);continue
        for f,ks in FAMILIES.items():
            missing=[k for k in ks if r['raw'][k] is None]
            if not missing:
                r['market_status'][f]='COMPLETE_REAL_QUOTES';continue
            if len(missing)>1:
                r['market_status'][f]='MULTIPLE_MISSING_QUOTES_UNDETERMINED'
                r['unresolved_markets'].append(f);continue
            m,kind,samples=_choose_margin(f,margins)
            if m is None:
                r['market_status'][f]='MARGIN_UNKNOWN_UNDETERMINED';r['unresolved_markets'].append(f);continue
            residual=1+m-sum(1/r['raw'][k] for k in ks if r['raw'][k] is not None)
            if residual<=.0005 or residual>=1:
                r['market_status'][f]='IMPUTATION_NOT_PLAUSIBLE';r['unresolved_markets'].append(f);continue
            point=1/residual
            if point<=1 or point>1000:
                r['market_status'][f]='IMPUTATION_OUT_OF_BOUNDS';r['unresolved_markets'].append(f);continue
            target=missing[0]
            # A data-driven range with wider floor for scarce same-family examples.
            widen=.015 if kind.startswith('SAME_FAMILY') and len(samples)>=4 else .035
            lo=max(-.005,min(samples)-widen) if samples else m-widen
            hi=min(.45,max(samples)+widen) if samples else m+widen
            recips=[1+mm-sum(1/r['raw'][k] for k in ks if k!=target) for mm in (lo,hi)]
            intervals=sorted([1/a for a in recips if .0005<a<1])
            r['effective_odds'][target]=round(point,5)
            r['estimated_quotes'][target]={
               'theoretical_odds':round(point,5),'source':'CALCULATED_NOT_OFFERED_BY_BOOKMAKER',
               'estimated_overround':round(m,6),'overround_source':kind,
               'estimated_odds_range':([round(intervals[0],3),round(intervals[-1],3)]
                                       if len(intervals)==2 else None),
               'warning':'This is NOT an iddaa offered odd or tradable quote.'}
            r['market_status'][f]='COMPLETE_WITH_ONE_THEORETICAL_QUOTE'
        output.append(r)
    return output

def market_probabilities(odds):
    out={}
    for f,ks in FAMILIES.items():
        if any(odds.get(k) is None for k in ks):
            out.update({k:None for k in ks});continue
        vals=[1/float(odds[k]) for k in ks];total=sum(vals)
        if not math.isfinite(total) or total<=0:raise OddsAuditError('INVALID_PROBABILITY_FAMILY')
        out.update({k:v/total for k,v in zip(ks,vals)})
    return out
