import json
from bson import ObjectId

def cid(s):
    return s.split(':')[-1]

# So dirty.
candidates = json.load(open('../parse_data/candidates.json'))
candidates_index = {candidate['id']: candidate for candidate in candidates}

constituencies = json.load(open('../parse_data/constituencies.json'))
constituencies_index = {cid(constituency['id']): constituency for constituency in constituencies}

def candidates(doc):
    resolved_candidates = []

    # Add candidates that users have added that the machine didn't find.
    for candidate_id in doc['user']['candidates']['confirm']:
        if not any([candidate_id == candidate['id'] for candidate in doc['possible']['candidates']]):
            candidate = candidates_index[candidate_id]
            candidate['state'] = 'confirmed'
            resolved_candidates.append(candidate)

    # Add candidates that the machine found.
    for candidate in doc['possible']['candidates']:
        candidate_state = 'unknown'

        if candidate['id'] in doc['user']['candidates']['confirm']:
            candidate_state = 'confirmed'
        elif candidate['id'] in doc['user']['candidates']['remove']:
            candidate_state = 'removed'

        candidate_ = candidates_index[candidate['id']]
        candidate_['state'] = candidate_state

        resolved_candidates.append(candidate_)

    return resolved_candidates

def constituencies(doc):
    resolved_constituencies = []
        
    doc['user']['constituencies']['confirm'] = map(cid, doc['user']['constituencies']['confirm'])
    doc['user']['constituencies']['remove'] = map(cid, doc['user']['constituencies']['remove'])

    # Add constituencies that users have added that the machine didn't find.
    for constituency_id in doc['user']['constituencies']['confirm']:
        if not any([constituency_id == constituency['id'] for constituency in doc['possible']['constituencies']]):
            constituency = constituencies_index[constituency_id]
            constituency['state'] = 'confirmed'
            resolved_constituencies.append(constituency)

    # Add constituencies that the machine found.
    for constituency in doc['possible']['constituencies']:
        constituency_state = 'unknown'

        if constituency['id'] in doc['user']['constituencies']['confirm']:
            constituency_state = 'confirmed'
        elif constituency['id'] in doc['user']['constituencies']['remove']:
            constituency_state = 'removed'

        constituency_ = constituencies_index[constituency['id']]
        constituency_['id'] = cid(constituency_['id'])
        constituency_['state'] = constituency_state

        resolved_constituencies.append(constituency_)

    return resolved_constituencies

def regenerate_matches(doc):
    """
        Generate the final description of the tags by combining the machine matched
        tags and the user contributed tags.
    """

    if 'possible' in doc:
        doc['candidates'] = candidates(doc)
        doc['constituencies'] = constituencies(doc) 

    return

if __name__ == "__main__":
    from pymongo import MongoClient

    client = MongoClient()
    db = client.news.articles

    for doc in db.find():
        regenerate_matches(doc)
        db.save(doc)

