import sys
import json

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from ppsay.article import get_articles
from ppsay.data import (
    get_candidates,
)

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles
db_candidates = db_client.news.candidates

export_data = {}

candidates = [x for x in get_candidates() if '2015' in x['candidacies']]

for i, candidate in enumerate(candidates):
    print >>sys.stderr, "{}/{}".format(i, len(candidates))

    article_docs = list(get_articles([candidate['id']]))
    
    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    export_data[candidate['id']] = [{'url': doc['page']['urls'][0],
                                     'title': doc['page']['title'],
                                     'source': doc.get('domain'),
                                     'date': doc['order_date'].isoformat(),} for doc in article_docs[:10]]

print json.dumps(export_data)

