"""
    Check that every article's pages exist.
"""

from ppsay.db import db_articles, db_pages

for article_doc in db_articles.find():
    if 'pages' not in article_doc:
        print article_doc['_id'], "MISSING PAGES"
        continue

    for page_id in article_doc['pages']:
        page_doc = db_pages.find_one({'_id': page_id})

        if page_doc is None:
            print page_id, "PAGE MISSING"


