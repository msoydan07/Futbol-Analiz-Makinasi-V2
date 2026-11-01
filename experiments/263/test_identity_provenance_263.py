"""Synthetic adversarial safety tests; no past-performance re-run."""
import copy
import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from identity_provenance_263 import (
    audit_registry_linkage, load_registry, IdentityProvenanceError, ID_NAMESPACE,
)

class IdentityProvenance263Tests(unittest.TestCase):
    def setUp(self):
        self.h=str(uuid.uuid5(ID_NAMESPACE, 'team:alpha'))
        self.a=str(uuid.uuid5(ID_NAMESPACE, 'team:beta'))
        self.row=dict(fixture_id='fx001',league='ENG1',season='2026-2027',match_date='2026-10-28',home_id=self.h,away_id=self.a)
        self.reg={'teams':{self.h:{'key':'alpha','name':'Alpha'},self.a:{'key':'beta','name':'Beta','verification':'FEDERATION_VERIFIED'}},'aliases':{'alpha':self.h,'beta':self.a},'fixtures':{'fx001':dict(self.row)},'external_fixtures':{}}
        self.source={'rows':1,'sha256':'a'*64}
    def audit(self, row=None, reg=None, source=None):
        return audit_registry_linkage([row or self.row],source or self.source,reg or self.reg,'b'*64)
    def test_registry_join_passes_but_not_live_verified(self):
        result=self.audit()
        self.assertEqual(result['historical_rows_linked'],1)
        self.assertEqual(result['status'],'OFFLINE_REGISTRY_LINKAGE_VALIDATED')
        self.assertFalse(result['independently_verified_official_fixture'])
        self.assertFalse(result['independently_verified_squad_or_lineups'])
        self.assertEqual(result['claimed_official_name_flags_not_rechecked'],1)
    def test_case_swap_rejected(self):
        with self.assertRaisesRegex(IdentityProvenanceError,'identity differs'):
            self.audit(row={**self.row,'home_id':self.a,'away_id':self.h})
    def test_unknown_fixture_rejected(self):
        with self.assertRaisesRegex(IdentityProvenanceError,'absent'):
            self.audit(row={**self.row,'fixture_id':'fx002'})
    def test_forged_uuid_rejected(self):
        bad=copy.deepcopy(self.reg);bad['teams'][self.h]['key']='different'
        with self.assertRaisesRegex(IdentityProvenanceError,'UUID'):
            self.audit(reg=bad)
    def test_unsafe_alias_rejected(self):
        bad=copy.deepcopy(self.reg);bad['aliases']['invented']='nobody'
        with self.assertRaisesRegex(IdentityProvenanceError,'Alias'):
            self.audit(reg=bad)
    def test_missing_fixture_rejected(self):
        bad=copy.deepcopy(self.reg);bad['fixtures']={}
        with self.assertRaises(IdentityProvenanceError):self.audit(reg=bad)
    def test_repeated_fixture_id_rejected(self):
        with self.assertRaisesRegex(IdentityProvenanceError,'Repeated'):
            audit_registry_linkage([self.row,self.row],{**self.source,'rows':2},self.reg,'b'*64)
    def test_source_row_count_rejected(self):
        with self.assertRaisesRegex(IdentityProvenanceError,'count mismatch'):
            self.audit(source={**self.source,'rows':9})
    def test_same_team_rejected(self):
        bad=copy.deepcopy(self.reg);bad['fixtures']['fx001']['away_id']=self.h
        with self.assertRaises(IdentityProvenanceError):self.audit(reg=bad)
    def test_read_bytes_sha_required_when_pinned(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'reg.json';f.write_text(json.dumps(self.reg),encoding='utf-8')
            digest=hashlib.sha256(f.read_bytes()).hexdigest()
            obj, got=load_registry(f, expected_sha256=digest)
            self.assertEqual(obj,self.reg);self.assertEqual(got,digest)
            with self.assertRaisesRegex(IdentityProvenanceError,'SHA-256 mismatch'):
                load_registry(f,expected_sha256='0'*64)

if __name__=='__main__':unittest.main()
