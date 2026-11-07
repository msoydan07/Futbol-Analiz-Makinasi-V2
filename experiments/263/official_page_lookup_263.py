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
    'ENG1': ('https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-season-2026-27', 'premierleague.com', 'epl'),
    'ENG2': ('https://www.efl.com/matches/', 'efl.com', 'jsonld'),
    'GER1': ('https://products.bundesliga.com/fixtures', 'bundesliga.com', 'dfl'),
    'ESP1': ('https://www.laliga.com/laliga-easports/resultados', 'laliga.com', 'jsonld'),
    'ITA1': ('https://en.legaseriea.it/serie-a/fixtures-results', 'legaseriea.it', 'jsonld'),
    'FRA1': ('https://ligue1.com/fr/articles/l1_article_5732-mpp-les-infos-de-la-journee-l1', 'ligue1.com', 'lfp_week10_2026'),
    'NED1': ('https://www.knvb.nl/competities/eredivisie/programma', 'knvb.nl', 'knvb'),
    'TUR1': ('https://www.tff.org/', 'tff.org', 'jsonld'),
    'POR1': ('https://www.ligaportugal.pt/calendar', 'ligaportugal.pt', 'jsonld'),
    'BEL1': ('https://www.proleague.be/', 'proleague.be', 'jsonld'),
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
    result=[]
    for row in markup.rows:
        # DFL: Matchday | Day | Date | Kick-off(CET) | Kick-off(UTC) | Home | Away | ...
        if len(row)<7:continue
        date=row[2];utctime=row[4];h=row[5];a=row[6]
        if not re.fullmatch(r'\d{2}-[A-Za-z]{3}-20\d\d',date):continue
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',utctime):continue
        try:dt=datetime.strptime(date+' '+utctime,'%d-%b-%Y %H:%M').replace(tzinfo=timezone.utc)
        except ValueError:continue
        result.append(_event(h,a,dt.date().isoformat(),dt.isoformat(),'dfl'))
    return result


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


def parse_official_events(league: str, html: str, parser: str|None=None) -> list[dict]:
    if league not in SOURCES:raise OfficialPageError('unsupported_league')
    if not isinstance(html,str) or len(html)>MAX_BYTES:raise OfficialPageError('invalid_official_response')
    m=_Markup();m.feed(html)
    kind=parser or SOURCES[league][2]
    funcs={'dfl':_dfl_events,'knvb':_knvb_events,'epl':_premier_events,'jsonld':_jsonld_events,'lfp_week10_2026':_lfp_week10_2026}
    if kind not in funcs:raise OfficialPageError('unsupported_parser')
    events=funcs[kind](m)
    # JSON-LD may supplement a site-specific parser, but never infer a fixture
    # from non-structured free text beyond the explicitly defined source format.
    if kind!='jsonld':events+=_jsonld_events(m)
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
    return end_url,data.decode('utf-8','replace')


def official_page_lookup(league, home, away, *, now=None, fetcher=None,
                         source_url=None, html=None, same_team=None):
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
        events=parse_official_events(league,html)
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
