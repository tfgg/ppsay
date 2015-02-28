import sys
from pymongo import MongoClient
from bson import ObjectId
import re
from collections import Counter

client = MongoClient()

articles = client.news.articles

doc_ids = [ObjectId(x) for x in sys.argv[1:]]

docs = [articles.find_one({'_id': doc_id}) for doc_id in doc_ids]

for doc in docs:
    print doc['page']['title'].encode('utf-8')

for doc in docs:
    print "  ", doc['keys'][0], [doc['page']['text'] == doc2['page']['text'] for doc2 in docs]

new_keys = set(sum([doc['keys'] for doc in docs], []))
new_urls = set(sum([doc['page']['urls'] for doc in docs], []))

new_user_candidates_confirm = []
for doc in docs:
    new_user_candidates_confirm += doc['user']['candidates']['confirm']

new_user_candidates_remove = []
for doc in docs:
    new_user_candidates_remove += doc['user']['candidates']['remove']

new_user_constituencies_confirm = []
for doc in docs:
    new_user_constituencies_confirm += doc['user']['constituencies']['confirm']

new_user_constituencies_remove = []
for doc in docs:
    new_user_constituencies_remove += doc['user']['constituencies']['remove']

new_user = {'candidates': {'confirm': list(set(new_user_candidates_confirm)),
                           'remove': list(set(new_user_candidates_remove)),},
            'constituencies': {'confirm': list(set(new_user_constituencies_confirm)),
                               'remove': list(set(new_user_constituencies_remove)),},}

docs[0]['keys'] = list(new_keys)
docs[0]['page']['urls'] = list(new_urls)
docs[0]['user'] = new_user

articles.save(docs[0])
print "  SAVING", docs[0]['_id']

for doc in docs[1:]:
    articles.remove({'_id': doc['_id']}, True)
    print "  DELETING", doc['_id']

