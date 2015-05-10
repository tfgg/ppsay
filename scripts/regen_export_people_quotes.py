# -*- coding: utf-8 -*-
import sys
import json
from collections import defaultdict

from ppsay.article import get_articles
from ppsay.data import (
    get_candidates,
    get_candidate,
)

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles

interesting_words = [
    'said', 'called', 'called on', 'says', 'promised', 'gaffe', 'popular',
    'mp', 'becoming', 'was', 'is', 'is the', 'worked', 'minister', 'councillor', 'hated', 'loved',
    'university', 'children', 'family', 'wife', 'husband', 'daughter', 'son', 'married',
    'apologised', 'apology', 'tackle', 'fix', 'moral', 'ethical', 'penalty', 'law',
    'responsible', 'pledge', 'urge', 'petition', 'received', u'£',
]

quotes = defaultdict(dict)

articles = db_articles.find({'quotes': {'$exists': True},
                             'state': 'approved',})

for i, article_doc in enumerate(articles):
    print >>sys.stderr, i

    for quote_doc in article_doc['quotes']:
        if article_doc['page']['date_published']:
            date = article_doc['page']['date_published'].isoformat()
        else:
            date = None

        score = 0.0

        for word in interesting_words:
            if word in quote_doc['text'].lower():
                score += 1.0

        words = quote_doc['text'].lower()
        #for word in blacklist:
        #    if word in words and len(quote_doc['candidates']) > 0:
                #print >>sys.stderr, "Blacklisted word:", word
                #print >>sys.stderr, " ".join([x['name'] for x in quote_doc['candidates']])
                #print >>sys.stderr, quote_doc['text']
                #print >>sys.stderr, "https://www.electionmentions.com/article/{}".format(article_doc['_id'])
                #print >>sys.stderr

        quote = {'html': quote_doc['html'],
                 'article': {'url': article_doc['page']['urls'][0],
                             'title': article_doc['page']['title'],
                             'domain': article_doc.get('domain'),
                             'date': date,
                             'id': str(article_doc['_id']),},
                 'score': score,}

        for person in quote_doc['candidates']:
            quotes[person['id']][quote_doc['text']] = quote

export_data = {}

for i, (person_id, person_quotes) in enumerate(quotes.items()):
    # Use dict to remove dupes
    quote_docs = sorted(person_quotes.values(), key=lambda x: x['score'], reverse=True)
    export_data[person_id] = quote_docs[:20]

print json.dumps(export_data, indent=4)

