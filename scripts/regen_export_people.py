import json

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

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

for candidate in get_candidates():
    article_docs = db_articles.find({'state': 'approved',
                                     'candidates': {'$elemMatch': {'id': candidate['id'], 'state': {'$ne': 'removed'}}}})

    article_docs = list(article_docs)
    for article_doc in article_docs:
        if article_doc['page']['date_published']:
            article_doc['order_date'] = article_doc['page']['date_published']
        else:
            article_doc['order_date'] = article_doc['time_added']
    
    
    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    export_data[candidate['id']] = [{'url': doc['page']['urls'][0],
                                     'title': doc['page']['title'],
                                     'source': doc.get('domain'),
                                     'date': doc['order_date'].isoformat(),} for doc in article_docs[:10]]

print json.dumps(export_data)

