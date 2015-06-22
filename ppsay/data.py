import json
from datetime import datetime
from os.path import realpath, join, dirname
from db import db_candidates

BASE_PATH = dirname(realpath(__file__))

def x(s):
    return join(BASE_PATH, s)

candidates = json.load(open(x('data/candidates.json')))
parties = json.load(open(x('data/parties.json')))
constituencies = json.load(open(x('data/constituencies.json')))
constituencies = sorted(constituencies, key=lambda x: x['name'])
constituencies_names = json.load(open(x('data/constituencies_other_names.json')))

candidates_index = {candidate['id']: candidate for candidate in candidates}
constituencies_index = {constituency['id']: constituency for constituency in constituencies}

try:
    squish_constituencies = json.load(open(x('data/squish_constituencies.json')))
except ValueError:
    squish_constituencies = {}

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
    'ge2010': {'date': datetime(2010, 5, 6),},
    'ge2015': {'date': datetime(2015, 5, 7),},
}
