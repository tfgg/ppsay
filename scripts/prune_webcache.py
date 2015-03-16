from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient()

db_webcache = client.news.web_cache
db_articles = client.news.articles

now = datetime.now()
last_week = now - timedelta(days=7)

didnt_wipe = 0
wiped = 0

for doc_webcache in db_webcache.find():
    if doc_webcache['time_fetched'] > last_week or doc_webcache['html'] is None:
        continue

    doc_article = db_articles.find_one({'keys': doc_webcache['url']})

    if doc_article is None:
        print u"WIPING", doc_webcache['_id'], doc_webcache['url'].encode('utf-8')
        doc_webcache['html'] = None
        db_webcache.save(doc_webcache)
        wiped += 1
    else:
        didnt_wipe += 1

print u"{} web cache objects wiped, {} web cache objects kept".format(wiped, didnt_wipe)

