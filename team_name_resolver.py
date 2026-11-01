"""Safe cross-source team-name resolution for the 10-league registry.

Never merge teams by fuzzy similarity. Add reviewed external names to
data/team_aliases_reviewed.csv (league,source_name,registry_name,source).
"""
import csv
from pathlib import Path
from identity import Registry,normalize

ALIASES=Path("data/team_aliases_reviewed.csv")
def resolve(registry,league,name,aliases_path=ALIASES):
 try:return registry.resolve_team(name)
 except KeyError:pass
 # Standard punctuation, diacritics and common legal suffixes; accept only a UNIQUE match.
 def key(value):
  import re,unicodedata
  s=unicodedata.normalize("NFKD",value.casefold().replace("ı","i"))
  s="".join(c for c in s if not unicodedata.combining(c))
  s=re.sub(r"[^a-z0-9]+","",s)
  for suffix in ("as","fk","sk"): 
   if s.endswith(suffix) and len(s)>len(suffix)+3:s=s[:-len(suffix)]
  return s
 matches={tid for alias,tid in registry.data["aliases"].items() if key(alias)==key(name)}
 if len(matches)==1:return next(iter(matches))
 if len(matches)>1:raise KeyError("Ambiguous normalized team name: "+name)
 p=Path(aliases_path)
 if p.exists():
  with p.open(encoding="utf-8-sig",newline="") as f:
   rows=list(csv.DictReader(f))
  hits=[row for row in rows if row["league"]==league and normalize(row["source_name"])==normalize(name)]
  ids={registry.resolve_team(row["registry_name"]) for row in hits}
  if len(ids)==1:return next(iter(ids))
  if len(ids)>1:raise KeyError("Conflicting reviewed aliases: "+name)
 raise KeyError("Unmapped team name (requires reviewed Maçkolik alias): "+name)
