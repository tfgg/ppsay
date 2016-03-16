from datetime import datetime
from collections import defaultdict
from bson import ObjectId
from db import db_articles, db_pages, db_stream
from ppsay.data import elections
from ppsay.page import Page
from ppsay.stream import StreamItem 

from matches import (
    add_matches,
    resolve_matches,
    resolve_quotes,
    add_quotes,
)
from ml.assign import get_machine

class ArticleTagged(object):
    priority = ['naive', 'machine', 'user',]

    def __init__(self):
        self.add = defaultdict(set)
        self.remove = defaultdict(set)

    def add(self, type, value):
        self.add[type].add(value)
    
    def remove(self, type, value):
        self.add[type].add(value)

    def resolve(self):
        out = set()

        for type in self.priority:
            for value in self.add[type]:
                out.add(value)

            for value in self.remove[type]:
                out.remove(value)

        return out 

    def as_dict(self):
        rtn = {
            type: {
                'add': list(self.add[type]),
                'remove': list(self.remove[type]),
            }
            for type in self.priority
        }
        rtn['final'] = self.resolve()
        return rtn


class Article(object):
    def __init__(self, doc=None):
        self.id = doc.get('_id')
        self.pages = doc['pages']
        self.time_added = doc['time_added']
        self.keys = doc['keys']
        self.analysis = doc['analysis']
        self.output = doc['output']
        self.state = doc['state']

    @classmethod
    def from_pages(klass, pages):
        doc = {
            'pages': [page._id for page in pages],
            'time_added': datetime.now(),
            'keys': [page.url for page in pages],
            'analysis': {},
            'output': {},
            'state': 'unsaved',
        }

        return klass(doc)
   
    @classmethod 
    def get_by_id(klass, article_id):
        doc = db_articles.find_one({'_id': ObjectId(article_id)})
        return klass(doc)
 
    def get_page(self):
        if not hasattr(self, '_page'):
            self._page = Page.get(self.pages[0])
        
        return self._page

    def process(self):
        page = self.get_page() 

        texts = [page.text, page.title,]

        self.analysis['matches'], self.analysis['possible'] = add_matches(texts)
        self.output['quotes'], self.output['tags'] = add_quotes(self.analysis['matches'], texts)
        
        self.analysis['machine'] = get_machine(self)

        resolve_matches(texts, self.analysis)
        resolve_quotes(texts, self.analysis, self.output)

    def as_dict(self):
        doc = {
            'pages': self.pages,
            'time_added': self.time_added,
            'keys': self.keys,
            'analysis': self.analysis,
            'output': self.output,
            'state': self.state,
        }
        
        if self.id is not None:
            doc['_id'] = self.id

        return doc

    def save(self):
        doc = self.as_dict()
        self.id = db_articles.save(doc)
        
        self.update_stream()

    def update_stream(self):
        stream_item = db_stream.find_one({'data.article_id': self.id})
    
        if stream_item is not None:
            stream_item_id = stream_item['_id']
        else:
            stream_item_id = None

        num_final_candidates = len([x for x in self.analysis['final']['candidates'] if x['state'] not in ['removed', 'removed_ml']])
        num_final_constituencies = len([x for x in self.analysis['final']['constituencies'] if x['state'] not in ['removed', 'removed_ml']])
       
        if num_final_candidates > 0 or num_final_constituencies > 0:
            stream_item = StreamItem.from_article(self)

            if stream_item_id:
                stream_item.id = stream_item_id

            stream_item.render()
            stream_item.save()
        elif stream_item is not None:
            db_stream.remove({'_id': stream_item['_id']})

