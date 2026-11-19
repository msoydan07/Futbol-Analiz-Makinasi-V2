"""Private repo xG transport: GitHub API doubles; no live token, no private payload."""
import base64
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import xg_private_repo_fetch_263 as bridge

class TestReadOnlyBridge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.checkout=self.root/"public";self.checkout.mkdir()
        self.target=self.root/"private"/"frozen.csv"
        columns=("fixture_id", "league", "date", "home_id", "away_id",
                 "home_goals", "away_goals", "home_xg", "away_xg",
                 "xg_source", "source_status")
        fp=io.StringIO(newline="")
        writer=csv.DictWriter(fp,fieldnames=columns)
        writer.writeheader()
        for i,l in enumerate(sorted((
            "ENG1","ENG2","GER1","ESP1","ITA1",
            "FRA1","NED1","TUR1","POR1","BEL1"))):
            writer.writerow(dict(fixture_id=str(i+1),league=l,date="2026-10-01",
                home_id="h",away_id="a",home_goals="0",away_goals="1",
                home_xg="1.25",away_xg="0.75",
                xg_source="xgEdge",source_status="VALID"))
        self.raw=fp.getvalue().encode("utf-8")
        self.sha256=hashlib.sha256(self.raw).hexdigest()
        self.blobsha=bridge._git_sha(self.raw)
        self.meta={"type":"file","path":bridge.PRIVATE_FILE,
                   "size":len(self.raw),"sha":self.blobsha,
                   "encoding":"none","content":""}
        self.blob={"sha":self.blobsha,"size":len(self.raw),
                   "encoding":"base64",
                   "content":base64.b64encode(self.raw).decode()}
        self.kw=dict(token="SUPER_PRIVATE_TOKEN_DO_NOT_DISPLAY",target=self.target,
            public_checkout=self.checkout,expected_sha=self.sha256,
            expected_size=len(self.raw),expected_rows=10)
    def tearDown(self):
        self.tmp.cleanup()

    @patch.object(bridge,"_get_json")
    def test_full_sha_scope_and_git_blob_check(self,get):
        get.side_effect=[self.meta,self.blob]
        out=bridge.retrieve(**self.kw)
        self.assertEqual(out["status"],bridge.READY)
        self.assertEqual(self.target.read_bytes(),self.raw)
        self.assertEqual(self.target.stat().st_mode & 0o777,0o600)
        self.assertNotIn("SUPER_PRIVATE_TOKEN",json.dumps(out))
        self.assertNotIn("home_xg",json.dumps(out))
        self.assertFalse(out["official_m4_modified"])
        self.assertEqual(get.call_count,2)
        self.assertIn("/git/blobs/",get.call_args_list[1].args[0])

    @patch.object(bridge,"_get_json")
    def test_no_credentials_do_not_call_network(self,get):
        out=bridge.retrieve(**{**self.kw,"token":""})
        self.assertEqual(out["status"],"PRIVATE_REPO_READ_TOKEN_NOT_CONFIGURED")
        get.assert_not_called()
        self.assertFalse(self.target.exists())

    @patch.object(bridge,"_get_json")
    def test_absent_remote_file_degrades_to_m4(self,get):
        get.side_effect=HTTPError("https://api.github.com",404,"not found",None,None)
        out=bridge.retrieve(**self.kw)
        self.assertEqual(out["status"],"PRIVATE_REPO_READ_UNAVAILABLE_KEEP_M4")
        self.assertFalse(self.target.exists())
        self.assertNotIn("SUPER_PRIVATE_TOKEN",str(out))

    @patch.object(bridge,"_get_json")
    def test_wrong_provider_blob_sha_fails_closed(self,get):
        wrong=dict(self.blob,sha="0"*40)
        get.side_effect=[self.meta,wrong]
        out=bridge.retrieve(**self.kw)
        self.assertEqual(out["status"],"PRIVATE_REPO_BLOB_METADATA_MISMATCH")
        self.assertFalse(self.target.exists())

    @patch.object(bridge,"_get_json")
    def test_different_locked_dataset_sha_fails_closed(self,get):
        get.side_effect=[self.meta,self.blob]
        out=bridge.retrieve(**{**self.kw,"expected_sha":"0"*64})
        self.assertEqual(out["status"],"PRIVATE_REPO_XG_LOCKED_SHA_MISMATCH")
        self.assertFalse(self.target.exists())

    @patch.object(bridge,"_get_json")
    def test_scope_mismatch_fails_closed(self,get):
        get.side_effect=[self.meta,self.blob]
        out=bridge.retrieve(**{**self.kw,"expected_rows":4618})
        self.assertEqual(out["status"],"PRIVATE_REPO_XG_SCHEMA_OR_SCOPE_REJECTED")
        self.assertFalse(self.target.exists())

    @patch.object(bridge,"_get_json")
    def test_read_only_fails_if_path_in_checkout(self,get):
        with self.assertRaisesRegex(ValueError,"INSIDE_PUBLIC_CHECKOUT"):
            bridge.retrieve(**{**self.kw,"target":self.checkout/"xg.csv"})
        get.assert_not_called()

    @patch.object(bridge,"_get_json")
    def test_existing_file_not_overwritten(self,get):
        self.target.parent.mkdir(parents=True)
        self.target.write_text("immutable")
        with self.assertRaisesRegex(ValueError,"ALREADY_EXISTS"):
            bridge.retrieve(**self.kw)
        self.assertEqual(self.target.read_text(),"immutable")
        get.assert_not_called()

if __name__=="__main__":
    unittest.main()
