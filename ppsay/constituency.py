from ppsay.db import db_candidates
from ppsay.data import elections

def constituency_get_candidates(constituency_id):
    candidate_docs = []
    for election_id in elections:
        query = {
                'deleted': False,
                'candidacies.{}.constituency.id'.format(election_id): constituency_id,
            }
        candidate_docs += list(db_candidates.find(
           query 
        ))

    candidate_docs = sorted(candidate_docs, key=lambda x: x['name'])

    return candidate_docs

def filter_candidate_or_incumbent(candidate_docs, constituency_id):
    person_ids = [
        x['id'] for x in candidate_docs \
        if ('ge2015' in x['candidacies'] and x['candidacies']['ge2015']['constituency']['id'] == str(constituency_id)) \
                     or x['incumbent']
    ]

    return person_ids


