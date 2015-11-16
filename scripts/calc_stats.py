from pymongo import MongoClient
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from ppsay.domains import get_domain
from ppsay.page import Page

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

docs = db_articles.find()

total_candidates = Counter()
last_week_candidates = Counter()
last_last_week_candidates = Counter()

domain_candidates = defaultdict(Counter)

total_constituencies = Counter()

one_week_ago = datetime.now() - timedelta(days=7)
two_week_ago = datetime.now() - timedelta(days=14)

for doc in docs:
    analysis = doc.get('analysis')

    if not analysis:
        continue

    if 'candidates' not in analysis['final']:
        continue

    if 'constituencies' not in analysis['final']:
        continue

    if 'state' not in doc:
        print "No state", doc['_id']
        continue
    
    print doc['keys'][0]

    if doc['state'] not in ['approved', 'whitelisted']:
        continue

    removed_states = ['removed', 'removed_ml']
    
    page = Page.get(doc['pages'][0])

    domain = get_domain(page.domain)

    for candidate in analysis['final']['candidates']:
        if candidate['state'] not in removed_states:
            total_candidates[candidate['id']] += 1

            if domain is not None and 'news' in domain['categories']:
                domain_candidates['national'][candidate['id']] += 1

            if domain is not None and 'local_news' in domain['categories']:
                domain_candidates['local'][candidate['id']] += 1
    
    for constituency in analysis['final']['constituencies']:
        if constituency['state'] not in removed_states:
            total_constituencies[constituency['id']] += 1

    if page.date_published is not None and page.date_published >= one_week_ago:
        for candidate in analysis['final']['candidates']:
            if candidate['state'] not in removed_states:
                last_week_candidates[candidate['id']] += 1
    
    if page.date_published is not None and one_week_ago > page.date_published >= two_week_ago:
        for candidate in analysis['final']['candidates']:
            if candidate['state'] not in removed_states:
                last_last_week_candidates[candidate['id']] += 1

total_rank = [cid for cid, c in sorted(total_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]

national_rank = [cid for cid, c in sorted(domain_candidates['national'].items(), key=lambda (candidate_id, count): count, reverse=True)]
local_rank = [cid for cid, c in sorted(domain_candidates['local'].items(), key=lambda (candidate_id, count): count, reverse=True)]

last_week_rank = [cid for cid, c in sorted(last_week_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]
last_last_week_rank = [cid for cid, c in sorted(last_last_week_candidates.items(), key=lambda (candidate_id, count): count, reverse=True)]

for candidate in db_candidates.find():
    candidate_id = candidate['id']

    candidate['mentions'] = {'total_count': 0,
                             'last_week_count': 0,
                             'last_last_week_count': 0,
                             'national_count': 0,
                             'local_count': 0,
                             'total_rank': None,
                             'last_week_rank': None,
                             'last_last_week_rank': None,
                            }

    if candidate_id in total_candidates:
        candidate['mentions']['total_count'] = total_candidates[candidate_id]
        candidate['mentions']['total_rank'] = total_rank.index(candidate_id)
    
    if candidate_id in domain_candidates['national']:
        candidate['mentions']['national_count'] = domain_candidates['national'][candidate_id]
        candidate['mentions']['national_rank'] = national_rank.index(candidate_id)
    
    if candidate_id in domain_candidates['local']:
        candidate['mentions']['local_count'] = domain_candidates['local'][candidate_id]
        candidate['mentions']['local_rank'] = local_rank.index(candidate_id)
    
    if candidate_id in last_week_candidates:
        candidate['mentions']['last_week_count'] = last_week_candidates[candidate_id]
        candidate['mentions']['last_week_rank'] = last_week_rank.index(candidate_id)
    
    if candidate_id in last_last_week_candidates:
        candidate['mentions']['last_last_week_count'] = last_last_week_candidates[candidate_id]
        candidate['mentions']['last_last_week_rank'] = last_last_week_rank.index(candidate_id)

    db_candidates.save(candidate)


