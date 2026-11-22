"""First-iddaa-PDF official verification through the current 10-league gateway.

The existing original PDF decoder / SHA and original football model are
unchanged. For each user PDF, one current official page per league (cached for
10 minutes), canonical team identity and strict kickoff are attempted FIRST.
Older per-team official adapter fallback is already guarded by the gateway.
No PDF listing is ever promoted to VERIFIED on its own.

A page that cannot be parsed only returns NOT_VERIFIED; the separate
source-graded PDF-only M4/C3 research path then proceeds independently.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timezone
from threading import Lock
from urllib.parse import urlparse

from sabah_official_fixture_gateway_263 import OfficialFixtureGateway
from mackolik_identity_gate_263 import _official


class OriginalPdfOfficialGateway:
    def __init__(self,*,gateway=None,clock=None):
        self.gateway=gateway or OfficialFixtureGateway(clock=clock)
        self.locks=defaultdict(Lock)

    def lookup(self,league,home,away):
        # A single official cached source for all rows of this league, even
        # if PDF matches are processed in parallel. Canonical verification is
        # carried out by the unchanged official batch gateway.
        with self.locks[league]:
            result=self.gateway.lookup(league,home,away)
        if not isinstance(result,dict) or result.get("status")!="VERIFIED":
            return {"status":"NOT_VERIFIED",
                    "reason":(result.get("reason") if isinstance(result,dict)
                              else "INVALID_OFFICIAL_GATE_RESULT"),
                    "gateway_status":result.get("status") if isinstance(result,dict) else None}
        if (result.get("league")!=league
            or not _official(result.get("source_url"),league)
            or not isinstance(result.get("kickoff_utc"),str)
            or not isinstance(result.get("retrieved_at_utc"),str)):
            return {"status":"NOT_VERIFIED","reason":"GATEWAY_EVIDENCE_INCOMPLETE"}
        # Names are the exact canonical names passed into the gateway,
        # WHICH has already independently verified observed official names
        # against those very same team IDs. We do NOT claim PDF as source.
        return {"status":"VERIFIED_OFFICIAL_FIXTURE",
                "home":home,"away":away,
                "kickoff_utc":result["kickoff_utc"],
                "retrieved_at_utc":result["retrieved_at_utc"],
                "source_url":result["source_url"],
                "source_origin":"CURRENT_OFFICIAL_PAGE_GATEWAY",
                "canonical_id_verified_by_gateway":True}
