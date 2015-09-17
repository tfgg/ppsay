from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_candidates = db_client.news.candidates

def constituency_get_candidates(constituency_id):
    candidate_docs = db_candidates.find({'deleted': {'$ne': True},
                                         '$or': [{"candidacies.ge2010.constituency.id": constituency_id},
                                                 {"candidacies.ge2015.constituency.id": constituency_id}]})

    candidate_docs = sorted(candidate_docs, key=lambda x: x['name'])

    return candidate_docs

def filter_candidate_or_incumbent(candidate_docs, constituency_id):
    person_ids = [x['id'] for x in candidate_docs \
                  if ('ge2015' in x['candidacies'] and x['candidacies']['ge2015']['constituency']['id'] == str(constituency_id)) \
                     or x['incumbent']]

    return person_ids


