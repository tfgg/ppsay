from ppsay.db import db_candidates, db_areas, db_domains
from bson.json_util import dumps

candidates = list(db_candidates.find())
areas = list(db_areas.find())
domains = list(db_domains.find())

out = {
    'candidates': candidates,
    'areas': areas,
    'domains': domains,
}
 
print dumps(out)

