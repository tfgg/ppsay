from ppsay.page import Page
from ppsay.db import db_articles

for doc in db_articles.find():
    d = doc['page']

    d['url'] = d['urls'][0]
    d['final_url'] = d['final_urls'][0]
    d['source'] = doc['source']
    d['domain'] = doc['domain']

    page = Page(d)

    print page.save()

    doc['pages'] = [page._id]
    del doc['page']
    del doc['source']
    del doc['domain']

    db_articles.save(doc)

