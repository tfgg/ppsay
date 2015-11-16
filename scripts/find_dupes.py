from pymongo import MongoClient
import re
#import Levenshtein
from collections import Counter, defaultdict

client = MongoClient()

db_articles = client.news.articles
db_pages = client.news.pages

docs = db_pages.find()

print "Grouping by title"
c = Counter()
for page in docs:
    c[page['title']] += 1

print "Building dict of duplicates"
docs = db_pages.find()

titles = defaultdict(list)

for page in docs:
    title = page['title']
    if title in c and c[title] > 1:
       titles[title].append(page)

print "Checking for body text dupes"
for title, pages in titles.items():
    if len(pages) > 1 and title != u"":
        print 
        print "#", title.encode('utf-8')
        
        page_ids = [page['_id'] for page in pages]

        docs_group = list(db_articles.find({'pages': {'$elemMatch': {'$in': page_ids}}}))
            
        if len(docs_group) == 1:
            print "Already merged"
            continue

        for page in pages:
            print u"  ", page['_id'], page['url'], [page['text'] == page2['text'] for page2 in pages]

        # Group together title matches by text matches
        same_text = defaultdict(list)

        for page in pages:
            same_text[page['text']].append(page)

        for text, pages in same_text.items():
            print u"  \"{} ...\": {}".format(repr(text[:100]), ", ".join([str(page['_id']) for page in pages]))

        for text, pages_group in same_text.items():
            if len(pages_group) == 1:
                continue

            page_ids = [page['_id'] for page in pages_group]

            docs_group = list(db_articles.find({'pages': {'$elemMatch': {'$in': page_ids}}}))
            
            if len(docs_group) == 1:
                print "Already merged"
                continue

            print u"  Merging", " ".join([str(doc['_id']) for doc in docs_group])

            new_keys = set(sum([doc['keys'] for doc in docs_group], []))
            new_pages = set(sum([doc['pages'] for doc in docs_group], []))
           
            new_user_candidates_confirm = []
            for doc in docs_group:
                new_user_candidates_confirm += doc['analysis']['user']['candidates']['confirm']
            
            new_user_candidates_remove = []
            for doc in docs_group:
                new_user_candidates_remove += doc['analysis']['user']['candidates']['remove']
            
            new_user_constituencies_confirm = []
            for doc in docs_group:
                new_user_constituencies_confirm += doc['analysis']['user']['constituencies']['confirm']
            
            new_user_constituencies_remove = []
            for doc in docs_group:
                new_user_constituencies_remove += doc['analysis']['user']['constituencies']['remove']

            new_user = {
                'candidates': {
                    'confirm': list(set(new_user_candidates_confirm)),
                    'remove': list(set(new_user_candidates_remove)),
                },
                'constituencies': {
                    'confirm': list(set(new_user_constituencies_confirm)),
                    'remove': list(set(new_user_constituencies_remove)),
                },
            }

            docs_group[0]['keys'] = list(new_keys)
            docs_group[0]['pages'] = list(new_pages)
            docs_group[0]['analysis']['user'] = new_user

            #db_articles.save(docs_group[0])
            print "  SAVING", docs_group[0]['_id']

            for doc in docs_group[1:]:
            #    db_articles.remove({'_id': doc['_id']}, True)
                print "  DELETING", doc['_id']

