"""Official-source fixture policy. A source URL is evidence, not proof of successful import."""
import json
from pathlib import Path
OFFICIAL={
"ENG1":{"authority":"Premier League","url":"https://www.premierleague.com/en/fixtures"},
"ENG2":{"authority":"English Football League","url":"https://www.efl.com/matches/"},
"GER1":{"authority":"Bundesliga / DFL","url":"https://www.bundesliga.com/en/bundesliga/matchday"},
"ESP1":{"authority":"LaLiga","url":"https://www.laliga.com/laliga-easports/calendario"},
"ITA1":{"authority":"Lega Serie A","url":"https://www.legaseriea.it/en/serie-a/fixture-and-results"},
"FRA1":{"authority":"Ligue 1 / LFP","url":"https://ligue1.com/matches"},
"NED1":{"authority":"Eredivisie","url":"https://eredivisie.nl/competitie/programma/"},
"TUR1":{"authority":"TFF","url":"https://www.tff.org/"},
"POR1":{"authority":"Liga Portugal","url":"https://www.ligaportugal.pt/"},
"BEL1":{"authority":"Pro League","url":"https://www.proleague.be/"}
}
def main():
 p=Path("data");p.mkdir(exist_ok=True)
 result={"version":"official_fixture_source_policy_v1","policy":"ONE_OFFICIAL_AUTHORITY_PER_LEAGUE","source_registry":OFFICIAL,"status":"SOURCE_REGISTRY_ONLY_NOT_IMPORTED","acceptance_rules":["Official league/federation fixture must be fetched and parsed successfully","Map both teams to immutable IDs; reject ambiguous names","Match existing unplayed fixtures if they exist; otherwise create future fixture candidates separately","Never classify historical completed results as unplayed fixtures","Record source URL and UTC retrieval timestamp","Use source-declared kickoff timezone; otherwise quarantine kickoff time","Recheck same official authority on match day","Report missing and unmatched fixtures, no guessed matches"],"second_independent_source_required":False}
 (p/"official_fixture_source_policy.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"sources":len(OFFICIAL),"status":result["status"]}))
if __name__=="__main__":main()
