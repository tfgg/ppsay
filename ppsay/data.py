import json
from datetime import datetime
from os.path import realpath, join, dirname
from db import db_candidates, db_areas

BASE_PATH = dirname(realpath(__file__))

def x(s):
    return join(BASE_PATH, s)

parties = json.load(open(x('data/parties.json')))

try:
    squish_constituencies = json.load(open(x('data/squish_constituencies.json')))
except ValueError:
    squish_constituencies = {}

def get_constituency(area_id):
    doc = db_areas.find_one({'id': area_id})

    del doc['_id']

    return doc

def get_constituencies():
    for area in db_areas.find():
        del area['_id']

        yield area

def get_candidate(candidate_id):
    doc = db_candidates.find_one({'id': candidate_id})

    del doc['_id']

    return doc

def get_candidates():
    for candidate in db_candidates.find():
        del candidate['_id']

        if 'deleted' in candidate and candidate['deleted']:
            continue

        yield candidate

elections = {
    'ge2010': {
        'date': datetime(2010, 5, 6),
        'type': 'ge'
    },
    'ge2015': {
        'date': datetime(2015, 5, 7),
        'type': 'ge'
    },
}
