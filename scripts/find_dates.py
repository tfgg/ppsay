import re
from pymongo import MongoClient
import lxml.html

client = MongoClient()

db_articles = client.news.articles
db_web_cache = client.news.web_cache

docs = db_articles.find()

for doc in docs:
    if not doc['page']:
        continue

    url = doc['page']['url']
    web_cache_doc = db_web_cache.find_one({'url': url})
    
    if web_cache_doc['html']:
        dates = find_dates(web_cache_doc['html']) 

        if dates:
            earliest_date = min(dates)

            doc['page']['date_published'] = earliest_date

            db_articles.save(doc)


