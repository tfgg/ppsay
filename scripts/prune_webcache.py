from pymongo import MongoClient
from datetime import datetime, timedelta
from ppsay.db import db_articles
from ppsay.page import Page

client = MongoClient()

db_webcache = client.news.web_cache
db_pages = client.news.articles

now = datetime.now()
last_week = now - timedelta(days=7)

didnt_wipe = 0
wiped = 0

for doc_webcache in db_webcache.find():
    if doc_webcache['time_fetched'] > last_week or (doc_webcache.get('html_compressed') is None and doc_webcache.get('html') is None):
        continue

    page = Page.get_url(doc_webcache['url'])

    if page is not None:
        doc_article = db_articles.find_one({'pages': page._id})
    else:
        doc_article = None

    if doc_article is None:
        print u"WIPING", doc_webcache['_id'], doc_webcache['url'].encode('utf-8')

        if 'html' in doc_webcache:
            doc_webcache['html'] = None

        if 'html_compressed' in doc_webcache:
            doc_webcache['html_compressed'] = None

        db_webcache.save(doc_webcache)
        wiped += 1
    else:
        didnt_wipe += 1

print u"{} web cache objects wiped, {} web cache objects kept".format(wiped, didnt_wipe)

