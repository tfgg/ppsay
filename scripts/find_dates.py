from ppsay.dates import add_date
import re
from pymongo import MongoClient
import lxml.html

client = MongoClient()

db_articles = client.news.articles
db_web_cache = client.news.web_cache

docs = db_articles.find()

for doc in docs:
    print doc['_id']

    if not doc['page']:
        continue

    if doc['page']['date_published']:
        continue

    doc['page']['date_published'] = add_date(doc)

    db_articles.save(doc)

