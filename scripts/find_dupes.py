from pymongo import MongoClient
import re
#import Levenshtein
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

    print title

    if title not in titles:
        titles[title] = []

    titles[title].append(doc)

titles = {title: docs for title, docs in titles.items() if len(docs) > 1}

for title, docs in titles.items():
    if len(docs) > 1 and title != u"":
        print title.encode('utf-8')

        for doc in docs:
            print "  ", doc['_id'], doc['keys'][0], [doc['page']['text'] == doc2['page']['text'] for doc2 in docs]

        same_text = {}

        for doc in docs:
            key = doc['page']['text']
            if key not in same_text:
                same_text[key] = []

            same_text[key].append(doc)

        #same_text = [doc1['page']['text'] == doc2['page']['text'] for doc1 in docs for doc2 in docs]

        #dists = []
        #for text1 in same_text:
        #    for text2 in same_text:
        #        dists.append(Levenshtein.distance(text1, text2) < 500)

        # Do something with this.

        for text, docs_group in same_text.items():
            if len(docs_group) == 1:
                continue

            print "  Merging", " ".join([str(doc['_id']) for doc in docs_group])

            new_keys = set(sum([doc['keys'] for doc in docs_group], []))
            new_urls = set(sum([doc['page']['urls'] for doc in docs_group], []))
            new_final_urls = set(sum([doc['page']['final_urls'] for doc in docs_group], []))
           
            new_user_candidates_confirm = []
            for doc in docs_group:
                new_user_candidates_confirm += doc['user']['candidates']['confirm']
            
            new_user_candidates_remove = []
            for doc in docs_group:
                new_user_candidates_remove += doc['user']['candidates']['remove']
            
            new_user_constituencies_confirm = []
            for doc in docs_group:
                new_user_constituencies_confirm += doc['user']['constituencies']['confirm']
            
            new_user_constituencies_remove = []
            for doc in docs_group:
                new_user_constituencies_remove += doc['user']['constituencies']['remove']

            new_user = {'candidates': {'confirm': list(set(new_user_candidates_confirm)),
                                       'remove': list(set(new_user_candidates_remove)),},
                        'constituencies': {'confirm': list(set(new_user_constituencies_confirm)),
                                           'remove': list(set(new_user_constituencies_remove)),},}

            #print new_keys
            #print new_urls
            #print new_user

            docs_group[0]['keys'] = list(new_keys)
            docs_group[0]['page']['urls'] = list(new_urls)
            docs_group[0]['page']['final_urls'] = list(new_final_urls)
            docs_group[0]['user'] = new_user

            articles.save(docs_group[0])
            print "  SAVING", docs_group[0]['_id']

            for doc in docs_group[1:]:
                articles.remove({'_id': doc['_id']}, True)
                print "  DELETING", doc['_id']

