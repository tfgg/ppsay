# -*- coding: utf-8 -*-
import sys
import json

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from ppsay.data import (
    get_candidates,
    get_candidate,
)

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles
db_candidates = db_client.news.candidates

interesting_words = [
    'said', 'called', 'called on', 'says', 'promised', 'gaffe', 'popular',
    'mp', 'becoming', 'was', 'is', 'is the', 'worked', 'minister', 'councillor', 'hated', 'loved',
    'university', 'children', 'family', 'wife', 'husband', 'daughter', 'son', 'married',
    'apologised', 'apology', 'tackle', 'fix', 'moral', 'ethical', 'penalty', 'law',
    'responsible', 'pledge', 'urge', 'petition', 'received', u'£',
]

export_data = {}

candidates = [x for x in get_candidates() if '2015' in x['candidacies']]

for i, candidate in enumerate(candidates):
    print >>sys.stderr, "{}/{}".format(i, len(candidates))

    article_docs = db_articles.find({'state': 'approved',
                                   'candidates': {'$elemMatch': {'id': candidate['id'], 
                                                                 'state': {'$ne': 'removed'}}}}) \
                              .sort([('time_added', -1)])

    # Use dict to remove dupes
    quote_docs = {}

    for article_doc in article_docs:
        for quote_doc in article_doc['quotes']:
            if candidate['id'] in [x[0] for x in quote_doc['candidate_ids']]:
                quote_doc['article'] = article_doc

                score = 0.0
                for word in interesting_words:
                    if word in quote_doc['text'].lower():
                        score += 1.0
                
                if article_doc['page']['date_published']:
                    date = article_doc['page']['date_published'].isoformat()
                else:
                    date = None

                quote = {'html': quote_doc['html'],
                         'article': {'url': article_doc['page']['urls'][0],
                                     'title': article_doc['page']['title'],
                                     'domain': article_doc.get('domain'),
                                     'date': date,
                                     'id': str(article_doc['_id']),},
                         'score': score,}

                quote_docs[quote['html']] = quote

    quote_docs = sorted(quote_docs.values(), key=lambda x: x['score'], reverse=True)
    export_data[candidate['id']] = quote_docs[:20]

print json.dumps(export_data, indent=4)

