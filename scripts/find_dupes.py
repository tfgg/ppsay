from pymongo import MongoClient
import re
from collections import Counter

client = MongoClient()

articles = client.news.articles

docs = articles.find()

titles = {}

#titles = Counter(doc['page']['title'] for doc in articles.find() if doc['page'])

for doc in docs:
    if not doc['page']:
        continue

    title = doc['page']['title']

    if title not in titles:
        titles[title] = []

    titles[title].append(doc)

for title, docs in titles.items():
    if len(docs) > 1 and title != u"":
        print title.encode('utf-8')

        for doc in docs:
            print "  ", doc['keys'][0], [doc['page']['text'] == doc2['page']['text'] for doc2 in docs]

        same_text = [doc1['page']['text'] == doc2['page']['text'] for doc1 in docs for doc2 in docs]

        if all(same_text):
            print "  Merging", " ".join([str(doc['_id']) for doc in docs])

            new_keys = set(sum([doc['keys'] for doc in docs], []))
            new_urls = set(sum([doc['page']['urls'] for doc in docs], []))
            new_final_urls = set(sum([doc['page']['final_urls'] for doc in docs], []))
           
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

            #print new_keys
            #print new_urls
            #print new_user

            docs[0]['keys'] = list(new_keys)
            docs[0]['page']['urls'] = list(new_urls)
            docs[0]['page']['final_urls'] = list(new_final_urls)
            docs[0]['user'] = new_user

            articles.save(docs[0])
            print "  SAVING", docs[0]['_id']

            for doc in docs[1:]:
                articles.remove({'_id': doc['_id']}, True)
                print "  DELETING", doc['_id']

