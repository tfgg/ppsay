from db import db_articles, db_pages
from ppsay.data import elections
from ppsay.page import Page

def get_articles(person_ids, constituency_ids=None):
    if constituency_ids:
        article_docs = db_articles.find({
            'state': 'approved',
            '$or': [{'constituencies': {'$elemMatch': {'id': {'$in': constituency_ids}, 'state': {'$ne': 'removed'}}}},
                    {'candidates': {'$elemMatch': {'id': {'$in': person_ids}, 'state': {'$nin': ['removed','removed_ml']}}}}]
        }).sort([
            ("time_added", -1),
        ])

    else:
        article_docs = db_articles.find({
            'state': 'approved',
            'candidates': {'$elemMatch': {'id': {'$in': person_ids}, 'state': {'$nin': ['removed','removed_ml']}}}
        }).sort([
            ('time_added', -1),
        ])


    article_docs = list(article_docs)

    for article_doc in article_docs:
        article_doc['page'] = Page.get(article_doc['pages'][0])

        if article_doc['page'].date_published:
            article_doc['order_date'] = article_doc['page'].date_published
        else:
            article_doc['order_date'] = article_doc['time_added']
        
        if article_doc['order_date'] <= elections['ge2010']['date']:
            article_doc['election'] = 'ge2010'
        else:
            article_doc['election'] = 'ge2015'


    return article_docs
