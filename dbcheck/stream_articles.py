"""
    Check that every article has a stream item.
"""

from ppsay.db import db_articles, db_stream

for article_doc in db_articles.find():
    stream_doc = db_stream.find_one({'data.article_id': article_doc['_id']})

    if stream_doc is None:
        print article_doc['_id'], "stream missing"


for stream_doc in db_stream.find():
    article_doc = db_articles.find_one({'_id': stream_doc['data']['article_id']})

    if article_doc is None:
        print stream_doc['data']['article_id'], "article missing"

