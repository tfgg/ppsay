from db import db_articles, db_pages, db_stream
from ppsay.data import elections
from ppsay.page import Page
from ppsay.stream import StreamItem 

from matches import add_matches, resolve_matches, add_quotes
from ml.assign import get_machine

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
        doc = db_articles.find_one({'_id': article_id})
        return klass(doc)
 
    def get_page(self):
        if not hasattr(self, '_page'):
            self._page = Page.get(self.pages[0])
        
        return self._page

    def process(self):
        page = self.get_page() 

        texts = [page.text, page.title,]

        self.analysis['matches'], self.analysis['possible'] = add_matches(texts)

        print self.analysis['matches']

        self.output['quotes'], self.output['tags'] = add_quotes(self.analysis['matches'], texts)
        
        self.analysis['machine'] = get_machine(self)

        resolve_matches(texts, self.as_dict())

        self.update_stream()

    def as_dict(self):
        return {
            '_id': self.id,
            'pages': self.pages,
            'time_added': self.time_added,
            'keys': self.keys,
            'analysis': self.analysis,
            'output': self.output,
            'state': self.state,
        }

    def save(self):
        doc = self.as_dict()
        self.id = db_articles.save(doc)

    def update_stream(self):
        stream_item = db_stream.find_one({'data.article_id': self.id})
    
        if stream_item:
            stream_item_id = stream_item['_id']
        else:
            stream_item_id = None
        
        stream_item = StreamItem.from_article(self)
        stream_item.render()
        stream_item.save()

        if stream_item:
            if stream_item_id is not None:
                stream_item['_id'] = stream_item_id
        
            db_stream.save(stream_item)

