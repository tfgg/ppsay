from pymongo import MongoClient
from collections import Counter

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

docs = db_articles.find()

candidates = Counter()
constituencies = Counter()

for doc in docs:
    print doc['keys'][0]

    if 'page' not in doc:
        continue
    
    if 'candidates' not in doc:
        continue

    if 'constituencies' not in doc:
        continue

    for candidate in doc['candidates']:
        candidates[candidate['id']] += 1
    
    for constituency in doc['constituencies']:
        constituencies[constituency['id']] += 1

for candidate_id, mention_count in candidates.items():
    candidate = db_candidates.find_one({'id': candidate_id})

    candidate['mentions'] = {'total_count': mention_count}

    db_candidates.save(candidate)

#print candidates
#print constituencies

