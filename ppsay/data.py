import pytz
import json
import iso8601
import re

from datetime import datetime
from os.path import realpath, join, dirname
from db import db_candidates, db_areas

BASE_PATH = dirname(realpath(__file__))

def x(s):
    return join(BASE_PATH, s)

parties = json.load(open(x("data/parties.json")))

try:
    squish_constituencies = json.load(open(x("data/squish_constituencies.json")))
except ValueError:
    squish_constituencies = {}

def get_constituency(area_id):
    doc = db_areas.find_one({"id": area_id})

    del doc["_id"]

    return doc

def get_constituencies():
    for area in db_areas.find():
        del area["_id"]

        yield area

def get_candidate(candidate_id):
    doc = db_candidates.find_one({"id": candidate_id})

    del doc["_id"]

    return doc

def get_candidates():
    for candidate in db_candidates.find():
        del candidate["_id"]

        if "deleted" in candidate and candidate["deleted"]:
            continue

        yield candidate

elections_data = json.load(open(x("data/elections.json")))

def get_election_id(x):
    if x == "2010":
        return "parl.2010-05-06"
    elif x == "2015":
        return "parl.2015-05-07"
    else:
        return x

def escape_election_id(x):
    return x.replace(".", "_")

def get_assembly(x):
    name = re.sub("([0-9]+)", "", x["name"]).strip()

    if x["organization"]:
        return x["organization"]["name"]
    elif "sp" in x["id"]:
        return "Scottish Parliament"
    elif "nia" in x["id"]:
        return "Northern Irish Assembly"
    elif "naw" in x["id"]:
        return "National Assembly of Wales"
    elif "gla" in x["id"]:
        return "Greater London Assembly"
    elif "pcc" in x["id"]:
        return "Police and Crime Commissioner"
    elif "mayor" in x["id"]:
        return "Mayor"
    elif "local" in x["id"]:
        return name.replace("local election", "").strip() + " Council"
    else:
        return None

elections = {
    escape_election_id(get_election_id(election['id'])): {
        'id': get_election_id(election['id']),
        'name': re.sub('([0-9]+)', '', election['name']).strip(),
        'date': iso8601.parse_date(election['election_date'],default_timezone=pytz.UTC),
        'assembly': get_assembly(election),
    }
    for election in elections_data['results'] 
}
