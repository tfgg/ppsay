import json
from os.path import realpath, join, dirname

BASE_PATH = dirname(realpath(__file__))

def x(s):
    return join(BASE_PATH, s)

candidates = json.load(open(x('../parse_data/candidates.json')))
parties = json.load(open(x('../parse_data/parties.json')))
constituencies = json.load(open(x('../parse_data/constituencies.json')))
constituencies_names = json.load(open(x('../parse_data/constituencies_other_names.json')))

candidates_index = {candidate['id']: candidate for candidate in candidates}
constituencies_index = {constituency['id']: constituency for constituency in constituencies}
