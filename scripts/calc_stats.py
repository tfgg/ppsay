from pymongo import MongoClient
from collections import Counter
from datetime import datetime, timedelta

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

docs = db_articles.find()

total_candidates = Counter()
last_week_candidates = Counter()
last_last_week_candidates = Counter()
total_constituencies = Counter()

one_week_ago = datetime.now() - timedelta(days=7)
two_week_ago = datetime.now() - timedelta(days=14)

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
    
    if doc['page']['date_published'] is not None and one_week_ago > doc['page']['date_published'] >= two_week_ago:
        for candidate in doc['candidates']:
            last_last_week_candidates[candidate['id']] += 1

total_rank = [cid for cid, c in sorted(total_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]
last_week_rank = [cid for cid, c in sorted(last_week_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]
last_last_week_rank = [cid for cid, c in sorted(last_last_week_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]

for candidate in db_candidates.find():
    candidate_id = candidate['id']

    candidate['mentions'] = {'total_count': 0,
                             'last_week_count': 0,
                             'last_last_week_count': 0,
                             'total_rank': None,
                             'last_week_rank': None,
                             'last_last_week_rank': None,
                            }

    if candidate_id in total_candidates:
        candidate['mentions']['total_count'] = total_candidates[candidate_id]
        candidate['mentions']['total_rank'] = total_rank.index(candidate_id)
    
    if candidate_id in last_week_candidates:
        candidate['mentions']['last_week_count'] = last_week_candidates[candidate_id]
        candidate['mentions']['last_week_rank'] = last_week_rank.index(candidate_id)
    
    if candidate_id in last_last_week_candidates:
        candidate['mentions']['last_last_week_count'] = last_last_week_candidates[candidate_id]
        candidate['mentions']['last_last_week_rank'] = last_last_week_rank.index(candidate_id)

    db_candidates.save(candidate)


