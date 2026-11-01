"""2.6.3: Maçkolik-named match -> immutable identity -> trusted on-demand official lookup.

Does not scrape Maçkolik, build fixture lists, invoke Module 0, or generate bets.
A MATCH NAME is not fixture evidence. Only a separately fetched and parsed official
observation from a trusted league/club adapter can verify a requested fixture.
"""
from __future__ import annotations
import csv
import importlib
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

VERSION = '263_mackolik_identity_gate_v1'
LEAGUE_ZONE = {
    'ENG1': 'Europe/London','ENG2': 'Europe/London',
    'GER1': 'Europe/Berlin','ESP1': 'Europe/Madrid',
    'ITA1': 'Europe/Rome','FRA1': 'Europe/Paris',
    'NED1': 'Europe/Amsterdam','TUR1': 'Europe/Istanbul',
    'POR1': 'Europe/Lisbon','BEL1': 'Europe/Brussels',
}
OFFICIAL_HOSTS = {
    'ENG1': {'premierleague.com'}, 'ENG2': {'efl.com'},
    'GER1': {'bundesliga.com'}, 'ESP1': {'laliga.com'},
    'ITA1': {'legaseriea.it'}, 'FRA1': {'ligue1.com','lfp.fr','psg.fr'},
    'NED1': {'eredivisie.nl','knvb.nl'}, 'TUR1': {'tff.org','bjk.com.tr'},
    'POR1': {'ligaportugal.pt'}, 'BEL1': {'proleague.be','kvmechelen.be'},
}
# Reuse the already-present official adapter modules; never create a parallel scraper.
OFFICIAL_ADAPTERS = {
    'ENG1':'premier_league_fixture_lookup','ENG2':'championship_fixture_lookup',
    'GER1':'bundesliga_fixture_lookup','ESP1':'laliga_fixture_lookup',
    'ITA1':'serie_a_fixture_lookup','FRA1':'ligue1_fixture_lookup',
    'NED1':'eredivisie_fixture_lookup','TUR1':'tff_fixture_lookup',
    'POR1':'portugal_fixture_lookup','BEL1':'belgium_fixture_lookup',
}


def key(name: str) -> str:
    """Only punctuation, Unicode and Turkish-I variants. NO fuzzy club merging."""
    if not isinstance(name, str) or not name.strip():
        return ''
    s = name.strip().replace('ı','i').replace('İ','I').casefold()
    s = ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    return re.sub('[^a-z0-9]','',s)


def _utc(s: str) -> datetime:
    if not isinstance(s,str) or not s:
        raise ValueError('timestamp_required')
    x=datetime.fromisoformat(s.replace('Z','+00:00'))
    if x.tzinfo is None:
        raise ValueError('timezone_required')
    return x.astimezone(timezone.utc)


def _official(url: object, league: str) -> bool:
    if not isinstance(url,str):return False
    p=urlparse(url)
    host=(p.hostname or '').lower()
    return (p.scheme=='https' and not p.username and not p.password
            and any(host==d or host.endswith('.'+d) for d in OFFICIAL_HOSTS[league]))


def _memberships(registry: dict, season: str) -> dict[str,set[str]]:
    """A verified read-only index OR the original canonical fixture registry.

    Historical membership is only team eligibility, NEVER fixture confirmation.
    """
    if registry.get('index_type') == 'CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1':
        return {league: set(ids) for league,ids in registry['season_memberships'].get(season,{}).items()}
    members=defaultdict(set)
    teams=registry['teams']
    for fixture in registry['fixtures'].values():
        league=fixture.get('league')
        if fixture.get('season')==season and league in LEAGUE_ZONE:
            for role in ('home_id','away_id'):
                tid=fixture.get(role)
                if tid in teams:members[league].add(tid)
    return members


def _validate_identity_source(registry: dict) -> None:
    """Refuse cache corruption and mismatched UUIDs; do not issue any new club IDs."""
    if not isinstance(registry,dict) or not all(isinstance(registry.get(x),dict) for x in ('teams','aliases')):
        raise ValueError('invalid_identity_registry')
    if registry.get('index_type') != 'CANONICAL_REGISTRY_READ_ONLY_IDENTITY_CACHE_V1':
        if not isinstance(registry.get('fixtures'),dict):
            raise ValueError('missing_original_registry_fixtures')
        return
    digest=registry.get('payload_sha256')
    if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):
        raise ValueError('identity_index_digest_missing')
    content={k:v for k,v in registry.items() if k!='payload_sha256'}
    payload=json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    if hashlib.sha256(payload).hexdigest()!=digest:
        raise ValueError('identity_index_payload_modified')
    if not re.fullmatch('[a-f0-9]{64}',str(registry.get('source_registry_sha256',''))):
        raise ValueError('canonical_registry_provenance_missing')
    from uuid import UUID, uuid5
    ns=UUID('0c312c79-42d1-4ca9-8b1c-4c65b96ef6b2')
    teams=registry['teams']
    if not teams or not isinstance(registry.get('season_memberships'),dict):
        raise ValueError('identity_index_empty')
    for tid, team in teams.items():
        key=team.get('key','') if isinstance(team,dict) else ''
        if not isinstance(key,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',key):
            raise ValueError('invalid_canonical_team_key')
        if str(uuid5(ns, f'team:{key}')) != tid:
            raise ValueError('canonical_team_uuid_mismatch')
    if any(tid not in teams for tid in registry['aliases'].values()):
        raise ValueError('dangling_team_alias')
    for season, leagues in registry['season_memberships'].items():
        if not re.fullmatch(r'\d{4}-\d{4}',season) or not isinstance(leagues,dict):
            raise ValueError('invalid_season_membership')
        for league,ids in leagues.items():
            if league not in LEAGUE_ZONE or not isinstance(ids,list) or len(ids)!=len(set(ids)) or any(t not in teams for t in ids):
                raise ValueError('invalid_team_membership')


def _reviewed(path: Path | None, registry: dict) -> dict[tuple[str,str],str]:
    """The existing reviewed Maçkolik list, if present; never invent mappings."""
    mapping={}
    if path is None or not path.is_file(): return mapping
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not {'league','source_name','registry_name','source'} <= set(reader.fieldnames or ()):
            raise ValueError('invalid_reviewed_alias_header')
        for row in reader:
            if key(row.get('source','')) not in {'mackolik','mackoliktv'}:
                continue
            league=row['league']; source_name=row['source_name']
            if league not in LEAGUE_ZONE or not key(source_name):
                raise ValueError('invalid_reviewed_alias')
            target_key=key(row['registry_name'])
            exact={tid for alias,tid in registry['aliases'].items() if key(alias)==target_key}
            if len(exact)!=1:
                raise ValueError('reviewed_alias_target_missing_or_ambiguous')
            tid=next(iter(exact))
            k=(league,key(source_name))
            if k in mapping and mapping[k]!=tid:
                raise ValueError('conflicting_reviewed_mackolik_alias')
            mapping[k]=tid
    return mapping


def _candidate_id(registry: dict, name: str, league: str, membership: dict[str,set[str]], reviewed:dict) -> str | None:
    normalized=key(name)
    exact={tid for alias,tid in registry['aliases'].items()
           if key(alias)==normalized and tid in membership.get(league,set())}
    reviewed_id=reviewed.get((league,normalized))
    if reviewed_id is not None and reviewed_id not in membership.get(league,set()):
        raise ValueError('reviewed_alias_not_in_league')
    if reviewed_id is not None:exact.add(reviewed_id)
    if len(exact)>1:
        raise ValueError('ambiguous_team_alias')
    return next(iter(exact)) if exact else None


def _variants(registry: dict, team_id: str, user_name: str) -> list[str]:
    official=registry['teams'][team_id]['name']
    # Include only names already registered to the exact same immutable team ID.
    aliases=[a for a,t in registry['aliases'].items() if t==team_id]
    aliases=sorted(aliases,key=lambda s:(len(s),s))
    candidates=[user_name,official,*aliases]
    seen=set();out=[]
    for s in candidates:
        v=key(s)
        if v and v not in seen:
            out.append(s);seen.add(v)
    return out[:4]


def resolve_requested_match(registry:dict, home:str, away:str, league:str|None,
                            season:str, reviewed:dict) -> dict:
    if not home.strip() or not away.strip():return {'status':'REJECTED','reason':'both_named_teams_required'}
    members=_memberships(registry,season)
    leagues=[league] if league in LEAGUE_ZONE else list(LEAGUE_ZONE) if league is None else []
    if not leagues:return {'status':'REJECTED','reason':'unsupported_league'}
    pairs=[];errors=[]
    for lg in leagues:
        try:
            h=_candidate_id(registry,home,lg,members,reviewed)
            a=_candidate_id(registry,away,lg,members,reviewed)
            if h and a and h!=a:pairs.append((lg,h,a))
            if h and a and h==a:errors.append('same_club')
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        return {'status':'REVIEW_REQUIRED','reason':sorted(set(errors))[0]}
    if len(pairs)!=1:
        return {'status':'REVIEW_REQUIRED', 'reason':'ambiguous_league' if pairs else 'unmapped_or_out_of_league',
                'candidate_leagues':[x[0] for x in pairs]}
    lg,h,a=pairs[0]
    return {'status':'RESOLVED_IDENTITY','league':lg,'season':season,'home_id':h,'away_id':a,
            'home_mackolik_name':home,'away_mackolik_name':away,
            'home_canonical_name':registry['teams'][h]['name'],
            'away_canonical_name':registry['teams'][a]['name']}


def _check_observation(observed:dict, identity:dict, registry:dict, membership:dict,
                       reviewed:dict,now:datetime) -> dict:
    lg=identity['league']
    if not isinstance(observed,dict) or observed.get('status') not in {'VERIFIED_OFFICIAL_FIXTURE','VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY'}:
        return {'status':'NOT_VERIFIED','reason':'official_fixture_not_confirmed'}
    # A trusted adapter must have actually fetched and parsed the official source.
    # Its returned names can be echoes of search arguments: NEVER rely on text alone.
    try:
        observed_home=_candidate_id(registry,observed['home'],lg,membership,reviewed)
        observed_away=_candidate_id(registry,observed['away'],lg,membership,reviewed)
        if (observed_home,observed_away)!=(identity['home_id'],identity['away_id']):
            raise ValueError('official_participants_mismatch')
        if not _official(observed['source_url'],lg):
            raise ValueError('non_official_source_url')
        retrieved=_utc(observed['retrieved_at_utc'])
        if retrieved>now+timedelta(minutes=5) or now-retrieved>timedelta(hours=24):
            raise ValueError('official_observation_outdated')
        if observed.get('status')=='VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY' and observed.get('kickoff_utc'):
            raise ValueError('date_only_status_conflicts_with_kickoff')
        if observed.get('kickoff_utc'):
            kickoff=_utc(observed['kickoff_utc'])
            if not now<=kickoff<=now+timedelta(days=7):
                raise ValueError('kickoff_outside_next_7_days')
            local=kickoff.astimezone(ZoneInfo(LEAGUE_ZONE[lg]))
            local_date=local.date().isoformat()
            time_status='CONFIRMED'
        else:
            raw=observed.get('match_date')
            local_date=date.fromisoformat(raw).isoformat()
            day=date.fromisoformat(local_date)
            if not now.astimezone(ZoneInfo(LEAGUE_ZONE[lg])).date()<=day<=\
                   (now+timedelta(days=7)).astimezone(ZoneInfo(LEAGUE_ZONE[lg])).date():
                raise ValueError('fixture_date_outside_window')
            kickoff=None; time_status='NOT_ANNOUNCED'
    except (KeyError,ValueError,TypeError,OverflowError) as e:
        return {'status':'NOT_VERIFIED','reason':str(e)[:120]}
    return {**identity,'status':'VERIFIED','fixture_source':'OFFICIAL_ON_DEMAND',
            'official_source_url':observed['source_url'],
            'retrieved_at_utc':retrieved.isoformat(),
            'kickoff_utc':kickoff.isoformat() if kickoff else None,
            'match_local_date':local_date,'kickoff_status':time_status,
            'analysis_date_cutoff_exclusive':local_date,
            'ready_for_data_audit':True,
            'official_source_parser_attested':True,
            'lineups_status':'NOT_CHECKED',
            'recommendation_eligible':False,
            'analysis_completed':False,
            'math_parameters_changed':False}


def prepare_from_mackolik_names(home:str,away:str,*,league:str|None=None,
                                season:str='2026-2027',registry_path:str|Path='experiments/263/evidence/identity_index_263.json',
                                reviewed_aliases_path:str|Path|None='data/team_aliases_reviewed.csv',
                                official_lookup=None, now:datetime|None=None) -> dict:
    """Accept user's two Maçkolik spellings; official lookup is separate and REQUIRED.

    official_lookup(home_name,away_name) must be a trusted adapter, not a chat/user
    supplied observation dictionary. Injection is for deterministic unit tests.
    On no unique official verification, fail closed and do not analyze.
    """
    if not isinstance(home,str) or not isinstance(away,str):
        return {'status':'REJECTED','reason':'named_teams_required'}
    if not isinstance(season,str) or not re.fullmatch(r'\d{4}-\d{4}',season):
        return {'status':'REJECTED','reason':'invalid_season'}
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        return {'status':'REJECTED','reason':'timezone_required'}
    now=now.astimezone(timezone.utc)
    try:
        registry=json.loads(Path(registry_path).read_text(encoding='utf-8'))
        _validate_identity_source(registry)
        reviewed=_reviewed(Path(reviewed_aliases_path) if reviewed_aliases_path else None,registry)
        resolved=resolve_requested_match(registry,home,away,league,season,reviewed)
        if resolved['status']!='RESOLVED_IDENTITY':return resolved
        lg=resolved['league']
        membership=_memberships(registry,season)
        if official_lookup is None:
            official_lookup=importlib.import_module(OFFICIAL_ADAPTERS[lg]).lookup
        if not callable(official_lookup):
            raise ValueError('trusted_official_lookup_required')
        homes=_variants(registry,resolved['home_id'],home)
        aways=_variants(registry,resolved['away_id'],away)
    except (ValueError,KeyError,OSError,UnicodeError,json.JSONDecodeError,ImportError) as e:
        return {'status':'REVIEW_REQUIRED','reason':str(e)[:120]}
    # Equal-index pairs first: user/user, official/official, short/short.
    # This prevents an eight-attempt limit from starving both-sided aliases.
    index_pairs = sorted(((i,j) for i in range(len(homes)) for j in range(len(aways))),
                         key=lambda ij:(max(ij),abs(ij[0]-ij[1]),ij[0]+ij[1]))[:8]
    attempts=0; failure_reasons=[]
    for i,j in index_pairs:
        h,a=homes[i],aways[j]
        attempts+=1
        try:
            observed=official_lookup(h,a)
        except Exception as e:
            failure_reasons.append('official_adapter_error:'+type(e).__name__)
            continue
        if not isinstance(observed,dict):
            failure_reasons.append('official_adapter_bad_payload')
            continue
        if observed.get('status') in ('VERIFIED_OFFICIAL_FIXTURE','VERIFIED_OFFICIAL_FIXTURE_DATE_ONLY'):
            checked=_check_observation(observed,resolved,registry,membership,reviewed,now)
            checked['official_lookup_attempts']=attempts
            # A successful observation with wrong participants or a bad source
            # must NOT trigger speculative searching for alternatives.
            return checked
        failure_reasons.append(str(observed.get('reason',observed.get('status','not_verified')))[:80])
    return {**resolved,'status':'NOT_VERIFIED',
            'reason':'official_match_not_confirmed',
            'official_lookup_attempts':attempts,
            'diagnostic_reasons':sorted(set(failure_reasons))[:5],
            'analysis_completed':False}


def prepare_mackolik_analysis_entry(home: str, away: str, **kwargs) -> dict:
    """Bridge verified on-demand identity into existing 2.6.3 pre-analysis context.

    No mathematical predictions, fixture selection, pilot or real-match ledger.
    When the official source has a date but no kickoff time, proceed to *data
    audit*, preserving kickoff status NOT_ANNOUNCED without inventing a clock.
    """
    result = prepare_from_mackolik_names(home, away, **kwargs)
    if result.get('status') != 'VERIFIED':
        return result
    if result['kickoff_utc'] is None:
        return {**result, 'status':'READY_FOR_DATA_AUDIT',
                'fixture_list_required':False,
                'facts':{kind:{'status':'NOT_CHECKED','math_effect':False}
                         for kind in ('lineups','injuries_suspensions','tactics')},
                'analysis_completed':False,'next_step':'LOAD_HISTORY_263',
                'note':'Official date verified; kickoff time not announced; no time inferred.'}
    # Re-use the already-tested evidence and lineup gate without fetching the
    # official match *twice*. Passing only the validated identity/source record.
    from on_demand_context_263 import prepare_named_match
    fixture={'status':'VERIFIED','league':result['league'],
             'home_id':result['home_id'],'away_id':result['away_id'],
             'kickoff_utc':result['kickoff_utc'],
             'source_url':result['official_source_url'],
             'retrieved_at_utc':result['retrieved_at_utc']}
    # Tests supply a fixed clock to this gate; live use derives a current UTC time.
    now=kwargs.get('now')
    ready=prepare_named_match(result['league'],home,away,now=now,
          registry_path=str(kwargs.get('registry_path','experiments/263/evidence/identity_index_263.json')),
          fixture_gate=lambda *_a,**_kw:fixture)
    if ready.get('status')!='READY_FOR_DATA_AUDIT':
        return {'status':'NOT_VERIFIED','reason':'263_context_gate_rejected_verified_fixture',
                'context_gate':ready}
    return {**ready,'mackolik_identity':result,
            'fixture_list_required':False,'next_step':'LOAD_HISTORY_263',
            'analysis_completed':False,'recommendation_eligible':False}