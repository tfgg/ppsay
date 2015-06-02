import bz2
import re
from pymongo import MongoClient
from newspaper import Article

client = MongoClient()

db_articles = client.news.articles
db_web_cache = client.news.web_cache

docs = db_articles.find()

for doc in docs:
    print doc['_id']

    if not doc['page']:
        continue

    url = doc['page']['urls'][0]
    web_cache_doc = db_web_cache.find_one({'url': url})
    
    if 'html_compressed' in web_cache_doc:
        article = Article(url=url)
        article.html = bz2.decompress(web_cache_doc['html_compressed'])
        article.is_downloaded = True
        article.parse()

        doc['page']['text'] = article.text
        print len(doc['page']['text'])

        db_articles.save(doc)


