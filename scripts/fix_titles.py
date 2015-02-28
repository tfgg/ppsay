from pymongo import MongoClient
import re

client = MongoClient()

articles = client.news.articles

docs = articles.find()

re_title = re.compile("(\(From.*?\))")

for doc in docs:
    if doc['page']:
        title = doc['page']['title'] 
        new_title = re_title.sub("", doc['page']['title']).strip()

        if title != new_title:
            doc['page']['title'] = new_title
            articles.save(doc)
 
