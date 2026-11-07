"""Experimental 2.6.3 official fixture page lookup; on demand, fail closed.

No cached fixture lists; user specifies teams. This parser proves only what a
freshly retrieved approved official page actually contains. It cannot guarantee
that any one official site exposes all fixtures. No prediction or betting logic.
"""
from __future__ import annotations
import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

VERSION = '263_official_page_lookup_v1_experimental'
# Current official schedule surfaces. These are source CANDIDATES, not guaranteed APIs.
SOURCES = {
    'ENG1': ('https://www.premierleague.com/en/news/4725574/fixture-amendments-for-premier-league-matches-in-november', 'premierleague.com', 'epl_nov26_confirmed'),
    'ENG2': ('https://www.efl.com/matches/', 'efl.com', 'jsonld'),
    'GER1': ('https://products.bundesliga.com/fixtures', 'bundesliga.com', 'dfl'),
    'ESP1': ('https://www.laliga.com/iframes/external-consumer-broadcast', 'laliga.com', 'laliga_broadcast_nov2026'),
    'ITA1': ('https://www.legaseriea.it/serie-a/news/le-designazioni-arbitrali-della-11a', 'legaseriea.it', 'seriea_j11_2026'),
    'FRA1': ('https://ligue1.com/fr/articles/l1_article_5732-mpp-les-infos-de-la-journee-l1', 'ligue1.com', 'lfp_week10_2026'),
    'NED1': ('https://www.knvb.nl/competities/eredivisie/programma', 'knvb.nl', 'knvb'),
    'TUR1': ('https://www.tff.org/default.aspx?ftxtID=2966&pageID=600', 'tff.org', 'tff_j11_2026'),
    'POR1': ('https://www.ligaportugal.pt/calendar', 'ligaportugal.pt', 'jsonld'),
    'BEL1': ('https://www.proleague.be/jpl-kalender!', 'proleague.be', 'belgium_proleague_nextjs_jpl'),
}
TIMEZONES = {'ENG1':'Europe/London','ENG2':'Europe/London','GER1':'Europe/Berlin',
 'ESP1':'Europe/Madrid','ITA1':'Europe/Rome','FRA1':'Europe/Paris',
 'NED1':'Europe/Amsterdam','TUR1':'Europe/Istanbul',
 'POR1':'Europe/Lisbon','BEL1':'Europe/Brussels'}
NL_MONTHS = dict(zip('januari februari maart april mei juni juli augustus september oktober november december'.split(), range(1,13)))
EN_MONTHS = dict(zip('january february march april may june july august september october november december'.split(), range(1,13)))
MAX_BYTES = 2_000_000

class OfficialPageError(ValueError): pass


def is_approved_url(url: str, league: str) -> bool:
    if league not in SOURCES or not isinstance(url,str): return False
    try:
        u = urlparse(url); host=(u.hostname or '').lower(); base=SOURCES[league][1]
        return (u.scheme=='https' and not u.username and not u.password and not u.port
                and host != '' and (host == base or host.endswith('.'+base)))
    except ValueError:
        return False


class _Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.row=None;self.cell=None
        self.visible=[];self.skip=0;self.jsonld=[];self.in_ld=False;self.ld=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='script' and d.get('type','').lower()=='application/ld+json':
            self.in_ld=True;self.ld=[];return
        if tag in ('script','style','noscript'):self.skip+=1
        if tag=='tr':self.row=[]
        if tag in ('td','th') and self.row is not None:self.cell=[]
        if tag in ('p','li','br','div','h1','h2','h3','h4','time','td','tr'):
            self.visible.append('\n')
    def handle_endtag(self,tag):
        if tag=='script' and self.in_ld:
            self.jsonld.append(''.join(self.ld));self.in_ld=False
            return
        if tag in ('script','style','noscript') and self.skip:self.skip-=1
        if tag in ('td','th') and self.cell is not None and self.row is not None:
            self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row);self.row=None
        if tag in ('p','li','div','td','tr','h1','h2','h3','h4'):self.visible.append('\n')
    def handle_data(self,data):
        if self.in_ld:self.ld.append(data)
        if not self.skip and not self.in_ld:
            self.visible.append(data)
            if self.cell is not None:self.cell.append(data)


def _event(home,away,match_date,kickoff=None,format_name=''):
    return {'home':str(home).strip(),'away':str(away).strip(),
            'match_date':str(match_date),'kickoff_utc':kickoff,'format':format_name}


def _timestamp(value):
    if not isinstance(value,str):return None,None
    if re.fullmatch(r'\d{4}-\d\d-\d\d',value):
        return value,None
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:return None,None
        return dt.date().isoformat(),dt.astimezone(timezone.utc).isoformat()
    except ValueError:return None,None


def _jsonld_events(markup):
    def walk(obj):
        if isinstance(obj,list):
            for item in obj:yield from walk(item)
        if isinstance(obj,dict):
            if 'SportsEvent' in (obj.get('@type') if isinstance(obj.get('@type'),list) else [obj.get('@type')]):
                yield obj
            for k in ('@graph','itemListElement','item','events'):
                if k in obj:yield from walk(obj[k])
    result=[]
    for value in markup.jsonld:
        try:obj=json.loads(value)
        except ValueError:continue
        for match in walk(obj):
            status=str(match.get('eventStatus','')).lower()
            if any(flag in status for flag in ('eventcancelled','eventpostponed','eventrescheduled')):
                continue
            h=match.get('homeTeam',{});a=match.get('awayTeam',{})
            if not isinstance(h,dict) or not isinstance(a,dict):continue
            date,kick=_timestamp(match.get('startDate'))
            if date and h.get('name') and a.get('name'):
                result.append(_event(h['name'],a['name'],date,kick,'jsonld'))
    return result


def _dfl_events(markup):
    """Bundesliga official live table: date/day composite cell, UTC-time cell."""
    result=[]
    if not any('Kick-off (UTC)' in ' '.join(row) and 'Home Team' in ' '.join(row)
               for row in markup.rows[:4]):return []
    for row in markup.rows:
        if len(row)<6:continue
        if len(row)>=7 and re.fullmatch(r'\d{2}-[A-Za-z]{3}-20\d\d',row[2]):
            date=row[2];utctime=row[4];h=row[5];a=row[6]
        else:
            dm=re.fullmatch(r'(?:Fri|Sat|Sun|Mon|Tue|Wed|Thu)\s*\|\s*(\d{2}-[A-Za-z]{3}-20\d\d)',row[1],re.I)
            if not dm:continue
            date=dm.group(1);utctime=row[3];h=row[4];a=row[5]
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',utctime):continue
        try:dt=datetime.strptime(date+' '+utctime,'%d-%b-%Y %H:%M').replace(tzinfo=timezone.utc)
        except ValueError:continue
        result.append(_event(h,a,dt.date().isoformat(),dt.isoformat(),'dfl'))
    return result


def _laliga_broadcast_nov2026(markup):
    """Official LA LIGA EA SPORTS broadcast table for 2026/27 round 12."""
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    if not any('Jornada 12 | 2026/2027' in x for x in lines):return []
    events=[]
    day=re.compile(r'^(?:VIE|SAB|DOM) (0[678])\.11\.2026$',re.I)
    time=re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d$')
    for i,x in enumerate(lines):
        m=day.fullmatch(x)
        if not m or i+4>=len(lines):continue
        if not time.fullmatch(lines[i+1]) or lines[i+3].upper()!='VS':continue
        home=lines[i+2];away=lines[i+4]
        if not home or not away or home==away:continue
        hr,mn=map(int,lines[i+1].split(':'))
        dt=datetime(2026,11,int(m.group(1)),hr,mn,tzinfo=ZoneInfo('Europe/Madrid'))
        events.append(_event(home,away,dt.date().isoformat(),
                             dt.astimezone(timezone.utc).isoformat(),'laliga_broadcast_nov2026'))
    return events


def _knvb_events(markup):
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    date=None;result=[]
    day_re=re.compile(r'^(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag) (\d{1,2}) (\w+) (20\d{2})$',re.I)
    for i,line in enumerate(lines):
        m=day_re.fullmatch(line)
        if m:
            try:date=datetime(int(m.group(3)),NL_MONTHS[m.group(2).lower()],int(m.group(1))).date()
            except (KeyError,ValueError):date=None
            continue
        if date and i+2<len(lines) and re.fullmatch(r'(?:[01]?\d|2[0-3]):[0-5]\d',lines[i+1]):
            # Explicit home -> time -> away sequence, no line-crossing guesses.
            home=line;away=lines[i+2]
            if home.lower() in ('image','afbeelding') or away.lower() in ('image','afbeelding'):continue
            try:
                local=datetime.fromisoformat(f'{date.isoformat()}T{lines[i+1]}:00').replace(tzinfo=ZoneInfo('Europe/Amsterdam'))
            except ValueError:continue
            result.append(_event(home,away,date.isoformat(),local.astimezone(timezone.utc).isoformat(),'knvb'))
    return result


def _premier_events(markup):
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    result=[];current=None;year=2026
    day_re=re.compile(r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\d{1,2}) (\w+)(?: (20\d{2}))?$',re.I)
    fixture_re=re.compile(r'^(?:(\d{1,2}:\d{2})(?: GMT| BST)? )?(.+?) v (.+?)(?: \([^()]*\))?(?:\*)?$',re.I)
    for line in lines:
        dm=day_re.fullmatch(line)
        if dm:
            month=EN_MONTHS.get(dm.group(2).lower())
            if not month:current=None;continue
            year=int(dm.group(3)) if dm.group(3) else 2027 if month<=6 else 2026
            try:current=datetime(year,month,int(dm.group(1))).date()
            except ValueError:current=None
            continue
        if not current:continue
        fm=fixture_re.fullmatch(line)
        if not fm:continue
        tm,h,a=fm.groups()
        # The official annual article is provisional: no published time => date-only.
        # Explicit times in a current live source are still rechecked before kickoff.
        utc=None
        if tm:
            local=datetime.fromisoformat(f'{current.isoformat()}T{tm}:00').replace(tzinfo=ZoneInfo('Europe/London'))
            utc=local.astimezone(timezone.utc).isoformat()
        result.append(_event(h,a,current.isoformat(),utc,'epl'))
    return result



def _lfp_week10_2026(markup):
    """Strict 5-Nov-2026 official J10 preview, never a season-long fixture feed."""
    lines=[' '.join(x.split()) for x in ''.join(markup.visible).splitlines() if x.strip()]
    if not any('MPP : Les infos de la J10' in x for x in lines):return []
    if not any('05/11/2026' in x for x in lines):return []
    heading=re.compile(r'^(vendredi|samedi|dimanche)\s+(\d{1,2})\s+novembre$',re.I)
    pair=re.compile(r'^(.+?)\s+[-–]\s+(.+?),\s*(vendredi|samedi|dimanche)\s+\((\d{1,2})h([0-5]\d)\)',re.I)
    ranks=re.compile(r'\s+\(\d{1,2}(?:e|er)\)$',re.I)
    days={'vendredi':6,'samedi':7,'dimanche':8}
    current=None;events=[]
    for line in lines:
        m=heading.fullmatch(line)
        if m:
            weekday=m.group(1).lower();d=int(m.group(2))
            current=(weekday,d) if days.get(weekday)==d else None
            continue
        if current is None:continue
        hit=pair.match(line)
        if not hit or hit.group(3).lower()!=current[0]:continue
        home=ranks.sub('',hit.group(1)).strip()
        away=ranks.sub('',hit.group(2)).strip()
        if not home or not away or home==away:continue
        try:
            local=datetime(2026,11,current[1],int(hit.group(4)),int(hit.group(5)),tzinfo=ZoneInfo('Europe/Paris'))
        except ValueError:continue
        events.append(_event(home,away,local.date().isoformat(),
                             local.astimezone(timezone.utc).isoformat(),
                             'lfp_week10_2026'))
    return events



def _seriea_j11_2026(markup):
    """Exact round-11 Italian official appointments; never infer year/weekday."""
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    whole=' '.join(lines).casefold()
    if not ('designazioni arbitrali' in whole and 'novembre' in whole and '2026' in whole and '11' in whole):
        return []
    pat=re.compile(r"^([A-ZÀ-Ü][A-ZÀ-Ü0-9 .’'-]{2,}?)\s+[–-]\s+([A-ZÀ-Ü][A-ZÀ-Ü0-9 .’'-]{2,}?)\s+(Venerdì|Sabato|Domenica)\s+([678])/11\s+h\.\s*(\d{1,2})[.:](\d{2})\b",re.I)
    weekday={6:'venerdì',7:'sabato',8:'domenica'}
    events=[]
    for line in lines:
        m=pat.match(line)
        if not m or m.group(3).casefold()!=weekday[int(m.group(4))]:continue
        try:
            dt=datetime(2026,11,int(m.group(4)),int(m.group(5)),int(m.group(6)),
                        tzinfo=ZoneInfo('Europe/Rome'))
        except ValueError:continue
        events.append(_event(m.group(1),m.group(2),dt.date().isoformat(),
                             dt.astimezone(timezone.utc).isoformat(),'seriea_j11_2026'))
    return events


def _tff_j11_2026(markup):
    """Exact TFF Super Lig week-11 rows, excluding all lower-division rows."""
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    def heading(value,division,week):
        return division in value.casefold() and bool(re.search(r'\b'+str(week)+r'\s*\.\s*hafta\b',value.casefold()))
    start=next((i for i,s in enumerate(lines)
                if heading(s,'trendyol süper lig',11)),None)
    if start is None:return []
    # TFF's DIV header is often split across HTML nodes. Its explicit
    # "Tarih / Ev Sahibi / Misafir" table header repeats before each
    # lower division, making the SECOND "Tarih" a robust league boundary.
    headers=[i for i in range(start+1,len(lines)) if lines[i].casefold()=='tarih']
    if len(headers)<2:return []
    first,second=headers[:2]
    if not any('trendyol 1. lig' in line.casefold() for line in lines[first+1:second]):
        return []
    heading_names=' '.join(lines[first+1:min(first+12,second)]).casefold()
    if not ('ev sahibi' in heading_names and 'misafir' in heading_names):
        return []
    segment=lines[first:second]
    dates=[(i,re.fullmatch(r'(0[678])\.11\.2026',s)) for i,s in enumerate(segment)
           if re.fullmatch(r'(0[678])\.11\.2026',s)]
    # The complete top flight round has nine fixtures; never accept a leak
    # across competition tables, but partial official HTML remains usable.
    if len(dates)>9:return []
    events=[]
    clock=re.compile(r'(?:[01]?\d|2[0-3]):[0-5]\d')
    for number,(i,day) in enumerate(dates):
        stop=dates[number+1][0] if number+1<len(dates) else len(segment)
        block=segment[i+1:stop]
        stamps=[(j,s) for j,s in enumerate(block) if clock.fullmatch(s)]
        if len(stamps)!=1:continue
        t,hm=stamps[0]
        following=block[t+1:]
        details=next((j for j,s in enumerate(following) if s.casefold()=='detaylar'),None)
        referees=next((j for j,s in enumerate(following) if re.match(r'^\(H\)\s',s,re.I)),len(following))
        if details is None or referees==len(following) or referees<=details:continue
        def teamlike(s):
            return (len(s)>=3 and not re.fullmatch(r'[-–]|\d+-\d+',s)
                    and not re.match(r'^\([A-Z]\)\s',s)
                    and s.casefold() not in ('detaylar','image'))
        home=[s for j,s in enumerate(following[:details]) if teamlike(s)]
        candidates=[s for s in following[details+1:referees] if teamlike(s)]
        if len(home)!=1 or len(candidates)<2:continue
        away=candidates[-1]
        if away==home[0] or any(x in away.casefold() for x in ('stadyum',' stadi',' stadium')):
            continue
        h,m=map(int,hm.split(':'))
        try:local=datetime(2026,11,int(day.group(1)),h,m,tzinfo=ZoneInfo('Europe/Istanbul'))
        except ValueError:continue
        events.append(_event(home[0],away,local.date().isoformat(),
                             local.astimezone(timezone.utc).isoformat(),'tff_j11_2026'))
    return events



def _epl_nov26_confirmed(markup):
    """November 2026 revised official TV schedule; explicit GMT 15:00 default."""
    lines=[' '.join(s.split()) for s in ''.join(markup.visible).splitlines() if s.strip()]
    joined=' '.join(lines).casefold()
    required=('fixture amendments for premier league matches in november',
              'november 2026',
              'all fixtures are gmt and are 15:00 kick-offs unless otherwise stated')
    if any(phrase not in joined for phrase in required):
        return _premier_events(markup)
    weekdays=re.compile(r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) ([0-9]{1,2}) November(?: 2026)?',re.I)
    games=re.compile(r'(?:([0-9]{1,2}:[0-9]{2}) )?(.+?) v (.+?)(?: \([^)]*\))?\*?',re.I)
    aliases={'leeds':'Leeds United','spurs':'Tottenham Hotspur',
             'newcastle':'Newcastle United',"nott'm forest":'Nottingham Forest',
             'man city':'Manchester City','man utd':'Manchester United',
             'bournemouth':'AFC Bournemouth','brighton':'Brighton & Hove Albion',
             'coventry':'Coventry City'}
    result=[];day=None
    for line in lines:
        date_match=weekdays.fullmatch(line)
        if date_match:
            day=int(date_match.group(1))
            continue
        if day is None:continue
        match=games.fullmatch(line)
        if not match:continue
        clock=match.group(1) or '15:00'
        home=match.group(2).strip()
        away=match.group(3).strip().rstrip('*').strip()
        home=aliases.get(home.casefold(),home)
        away=aliases.get(away.casefold(),away)
        if home==away:continue
        hour,minute=map(int,clock.split(':'))
        try:utc=datetime(2026,11,day,hour,minute,tzinfo=timezone.utc)
        except ValueError:continue
        result.append(_event(home,away,utc.date().isoformat(),utc.isoformat(),
                             'epl_nov26_confirmed'))
    return result


def parse_official_events(league: str, html: str, parser: str|None=None) -> list[dict]:
    if league not in SOURCES:raise OfficialPageError('unsupported_league')
    if not isinstance(html,str) or len(html)>MAX_BYTES:raise OfficialPageError('invalid_official_response')
    kind=parser or SOURCES[league][2]
    if kind=="efl_2026_27_official_tv_selection":
        from sabah_eng2_official_tv_263 import parse_efl_tv
        return parse_efl_tv(html)
    m=_Markup();m.feed(html)
    from sabah_portugal_official_news_263 import PARSER as POR_NEWS_PARSER,parse_news
    from sabah_belgium_official_nextjs_263 import PARSER as BEL_NEWS_PARSER,parse_proleague
    funcs={BEL_NEWS_PARSER:lambda _m:parse_proleague(html),
           POR_NEWS_PARSER:lambda _m:parse_news(html),
           'dfl':_dfl_events,'knvb':_knvb_events,'epl':_premier_events,
           'jsonld':_jsonld_events,'lfp_week10_2026':_lfp_week10_2026,
           'seriea_j11_2026':_seriea_j11_2026,'tff_j11_2026':_tff_j11_2026,
           'epl_nov26_confirmed':_epl_nov26_confirmed,
           'laliga_broadcast_nov2026':_laliga_broadcast_nov2026}
    if kind not in funcs:raise OfficialPageError('unsupported_parser')
    events=funcs[kind](m)
    # JSON-LD may supplement a site-specific parser, but never infer a fixture
    # from non-structured free text beyond the explicitly defined source format.
    if kind not in ('jsonld','tff_j11_2026','seriea_j11_2026','epl_nov26_confirmed',POR_NEWS_PARSER,BEL_NEWS_PARSER):
        events+=_jsonld_events(m)
    unique={}
    for e in events:
        if not e['home'] or not e['away']:continue
        key=(e['home'],e['away'],e['match_date'],e['kickoff_utc'])
        unique[key]=e
    return list(unique.values())


class _OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,league):self.league=league
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not is_approved_url(newurl,self.league):
            raise OfficialPageError('redirect_outside_official_domain')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def _default_fetch(url,league):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (fixture verification)', 'Accept':'text/html'})
    opener=urllib.request.build_opener(_OfficialRedirect(league))
    with opener.open(req,timeout=15) as res:
        end_url=res.geturl()
        ctype=res.headers.get('Content-Type','')
        if 'html' not in ctype and 'text/plain' not in ctype:
            raise OfficialPageError('non_html_official_content')
        data=res.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise OfficialPageError('official_page_too_large')
    try:
        html=data.decode('utf-8')
    except UnicodeDecodeError:
        if league!='TUR1':raise OfficialPageError('non_utf8_official_response')
        html=data.decode('windows-1254','replace')
    return end_url,html


def official_page_lookup(league, home, away, *, now=None, fetcher=None,
                         source_url=None, html=None, same_team=None,parser=None):
    """Search one authorized official page ONLY, not a cached fixture list.

    same_team(observed_name, requested_name) resolves BOTH to identical canonical
    IDs. It is mandatory: a normalization or approximate name guess is unsafe.
    """
    if league not in SOURCES:return {'status':'REJECTED','reason':'unsupported_league'}
    if not isinstance(home,str) or not isinstance(away,str) or not home.strip() or not away.strip():
        return {'status':'REJECTED','reason':'named_match_required'}
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:return {'status':'REJECTED','reason':'timezone_required'}
    now=now.astimezone(timezone.utc)
    if not callable(same_team):return {'status':'REJECTED','reason':'canonical_team_matcher_required'}
    url=source_url or SOURCES[league][0]
    if not is_approved_url(url,league):return {'status':'REJECTED','reason':'unapproved_official_url'}
    supplied_html = html is not None
    try:
        if html is None:
            redirected,html=fetcher(url) if fetcher else _default_fetch(url,league)
            if not is_approved_url(redirected,league):raise OfficialPageError('redirect_outside_official_domain')
        events=parse_official_events(league,html,parser=parser)
    except (OfficialPageError,ValueError,UnicodeError,OSError,TimeoutError) as exc:
        return {'status':'NOT_VERIFIED','reason':'official_source_parse_or_fetch_error','detail':str(exc)[:160]}
    matched=[]
    for event in events:
        try:
            if same_team(event['home'],home) and same_team(event['away'],away):matched.append(event)
        except (KeyError,ValueError,TypeError):pass
    if not matched:
        return {'status':'NOT_VERIFIED','reason':'requested_fixture_not_observed_on_this_page',
                'source_url':url,'events_parsed':len(events), 'does_not_prove_no_fixture':True}
    # No silent choice where duplicate or conflicting kickoff/date observations exist.
    if len(matched)!=1:return {'status':'REVIEW_REQUIRED','reason':'ambiguous_or_conflicting_official_observations','count':len(matched)}
    m=matched[0]
    # Premier League annual fixture release is explicitly subject to amendment;
    # a displayed time is NOT treated as independently re-confirmed match-day time.
    annual_release = m['format']=='epl'
    if m['kickoff_utc'] and not annual_release:
        try:kick=datetime.fromisoformat(m['kickoff_utc']).astimezone(timezone.utc)
        except ValueError:return {'status':'NOT_VERIFIED','reason':'invalid_kickoff'}
        if not now<=kick<=now+timedelta(days=7):return {'status':'OUTSIDE_WINDOW','reason':'kickoff_outside_7_days'}
        status='VERIFIED_OFFICIAL_FIXTURE'; kick_utc=kick.isoformat()
    else:
        # Calendar date without a confirmed time is *not* a guessed kickoff.
        from datetime import date
        day=date.fromisoformat(m['match_date'])
        if not now.astimezone(ZoneInfo(TIMEZONES[league])).date()<=day<=\
           (now+timedelta(days=7)).astimezone(ZoneInfo(TIMEZONES[league])).date():
            return {'status':'OUTSIDE_WINDOW','reason':'date_outside_7_days'}
        status='VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY';kick_utc=None
    return {'status':status,'home':m['home'],'away':m['away'], 'match_date':m['match_date'],
            'kickoff_utc':kick_utc,'source_url':url,'retrieved_at_utc':now.isoformat(),
            'source_parser':m['format'],'source_origin':'INJECTED_HTML_TEST_ONLY' if supplied_html else 'FETCHED_OFFICIAL_PAGE',
            'provisional_schedule_notice':annual_release,
            'listed_time_unreconfirmed':bool(annual_release and m['kickoff_utc'])}


def coverage_inventory():
    # A configured URL/structured parser is NOT a proven operational adapter.
    return {lg:{'source_url':u,'format':fmt,
                'coverage_status':'PARSER_IMPLEMENTED_NOT_LIVE_CONFIRMED' if fmt in ('dfl','knvb','epl','lfp_week10_2026')
                else 'JSONLD_DISCOVERY_ONLY_NOT_GUARANTEED',
                'all_fixtures_covered':False}
            for lg,(u,host,fmt) in SOURCES.items()}
