from pymongo import MongoClient
from collections import Counter
from datetime import datetime, timedelta

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

docs = db_articles.find()

total_candidates = Counter()
last_week_candidates = Counter()
total_constituencies = Counter()

one_week_ago = datetime.now() - timedelta(days=7)

for doc in docs:
    print doc['keys'][0]

    if 'page' not in doc:
        continue
    
    if 'candidates' not in doc:
        continue

    if 'constituencies' not in doc:
        continue

    for candidate in doc['candidates']:
        total_candidates[candidate['id']] += 1
    
    for constituency in doc['constituencies']:
        total_constituencies[constituency['id']] += 1

    if doc['page']['date_published'] is not None and doc['page']['date_published'] >= one_week_ago:
        for candidate in doc['candidates']:
            last_week_candidates[candidate['id']] += 1

for candidate in db_candidates.find():
    candidate_id = candidate['id']

    candidate['mentions'] = {'total_count': 0,
                             'last_week_count': 0,}

    if candidate_id in total_candidates:
        candidate['mentions']['total_count'] = total_candidates[candidate_id]
    
    if candidate_id in last_week_candidates:
        candidate['mentions']['last_week_count'] = last_week_candidates[candidate_id]

    db_candidates.save(candidate)


