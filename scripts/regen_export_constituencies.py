import json

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    get_candidate,
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

constituency_ids = constituencies_index.keys()

for constituency_id in constituency_ids:
    candidate_docs = db_candidates.find({'deleted': {'$ne': True},
                                       '$or': [{"candidacies.2010.constituency.id": str(constituency_id)},
                                               {"candidacies.2015.constituency.id": str(constituency_id)}]})

    candidate_docs = sorted(candidate_docs, key=lambda x: x['name'])

    candidate_ids = [x['id'] for x in candidate_docs if ('2015' in x['candidacies'] and x['candidacies']['2015']['constituency']['id'] == str(constituency_id)) \
                                                       or x['incumbent']]

    article_docs = db_articles.find({'state': 'approved',
                                   '$or': [{'constituencies': {'$elemMatch': {'id': str(constituency_id), 'state': {'$ne': 'removed'}}}},
                                           {'candidates': {'$elemMatch': {'id': {'$in': candidate_ids}, 'state': {'$ne': 'removed'}}}}]}) \

    article_docs = list(article_docs)
    for article_doc in article_docs:
        if article_doc['page']['date_published']:
            article_doc['order_date'] = article_doc['page']['date_published']
        else:
            article_doc['order_date'] = article_doc['time_added']
    
    
    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    export_data[constituency_id] = [{'url': doc['page']['urls'][0],
                                     'title': doc['page']['title'],
                                     'source': doc.get('domain'),
                                     'date': doc['order_date'].isoformat(),} for doc in article_docs[:10]]

print json.dumps(export_data)

