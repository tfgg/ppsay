import json

candidates = json.load(open('parse_data/candidates.json'))
parties = json.load(open('parse_data/parties.json'))
constituencies = json.load(open('parse_data/constituencies.json'))
constituencies_names = json.load(open('parse_data/constituencies_other_names.json'))

candidates_index = {candidate['id']: candidate for candidate in candidates}
constituencies_index = {constituency['id']: constituency for constituency in constituencies}
