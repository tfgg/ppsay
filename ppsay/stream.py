import pytz

from bson import ObjectId
from ppsay.db import db_articles, db_pages, db_stream
from ppsay.page import Page

from flask import render_template

class StreamItem(object):
    templates_types = {
        'article': 'stream/article_item.html',
    }

    def __init__(self, doc=None):
        self.id = doc.get('_id')
        self.type = doc['type']
        self.data = doc['data']
        self.streams = doc['streams']
        self.date_order = doc['date_order'].replace(tzinfo=pytz.UTC)
        self.html_cached = doc['html_cached']

    def as_dict(self):
        doc = {
            'type': self.type,
            'data': self.data,
            'streams': self.streams,
            'date_order': self.date_order,
            'html_cached': self.html_cached,
        }

        print doc

        if self.id is not None:
            doc['_id'] = self.id

        return doc

    def save(self):
        self.id = db_stream.save(self.as_dict())
        return self.id

    def render(self):
        pass

    @classmethod
    def get_all(klass, num=None):
        stream = db_stream.find().sort([('date_order', -1)])

        if num is not None:
            stream = stream.limit(num)

        return [StreamItem(item) for item in stream]

    @classmethod
    def get_since(klass, datetime_since):
        stream = db_stream.find({'date_order': {'$gt': datetime_since}})

        return [StreamItem(item) for item in stream]

    @classmethod
    def get_by_entities(klass, num=None, person_ids=None, constituency_ids=None):
        if person_ids is None:
            person_ids = []

        if constituency_ids is None:
            constituency_ids = []

        if person_ids or constituency_ids:
            stream = db_stream.find({
                '$or': [
                    {'streams.constituencies': {'$in': constituency_ids}},
                    {'streams.people': {'$in': person_ids}},
                ],
            })
        else:
            stream = db_stream.find()

        stream = stream.sort([('date_order', -1)])

        if num is not None:
            stream = stream.limit(num)

        return [StreamItem(item) for item in stream]

    @classmethod
    def from_article(klass, article):
        if article.pages is None:
            print "NO PAGES"
            return None

        page = article.get_page()

        if page.date_published:
            order_date = page.date_published
        else:
            order_date = article.time_added

        order_date = order_date.replace(tzinfo=pytz.UTC)

        if len(article.output['quotes']) > 0:
            quote = {
                'html': article.output['quotes'][0]['html'],
                'truncated': article.output['quotes'][0]['truncated'],
            }
        else:
            quote = None

        doc = {
            'type': 'article',
            'data': {
                'article_id': article.id,
                'url': page.url,
                'title': page.title,
                'domain': page.domain,
                'date_published': page.date_published,
                'quote': quote,
                'people': [
                    {
                        'id': candidate['id'],
                        'name': candidate['name'],
                    }
                    for candidate
                    in article.analysis['final']['candidates']
                    if candidate['state'] in ['confirmed_ml', 'confirmed',]
                ],
                'constituencies': [
                    {
                        'id': constituency['id'],
                        'name': constituency['name'],
                    }
                    for constituency
                    in article.analysis['final']['constituencies']
                    if constituency['state'] in ['confirmed','unknown']
                ],
            },
            'streams': {
                'people': [
                    candidate['id']
                    for candidate in article.analysis['final']['candidates']
                    if candidate['state'] in ['confirmed_ml', 'confirmed',]
                ],
                'constituencies': [
                    constituency['id']
                    for constituency in article.analysis['final']['constituencies']
                    if constituency['state'] in ['confirmed','unknown']
                ],
            },
            'html_cached': None,
            'date_order': order_date, 
        }

        return klass(doc)

