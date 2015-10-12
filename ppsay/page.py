import sys
import re

from urlparse import urlparse

from webcache import WebPage
from newspaper import Article as NewspaperArticle
from ppsay.data import elections
from ppsay.dates import find_dates_tree

from db import db_pages

def fix_title(s):
    return re_title.sub("", s).strip()

re_title = re.compile("(\(From.*?\))")

class Page(object):
    class FetchError(Exception):
        pass

    class ParseError(Exception):
        pass

    def __init__(self, doc=None):
        self._id = None

        if doc is not None:
            self._from_doc(doc)

    def _from_doc(self, doc):
        if '_id' in doc:
            self._id = doc['_id']

        self.domain = doc['domain']
        self.source = doc['source']
        self.url = doc['url']
        self.url_final = doc['final_url']
        self.title = doc['title']
        self.text = doc['text']
        self.date_published = doc['date_published']

    @classmethod
    def from_web_page(klass, web_page, source):
        page = klass()

        page.url = web_page.url

        if web_page.html is None:
            raise Page.FetchError(u"HTML field empty on {}".format(page.url))

        page.url_final = web_page.final_url

        parser = page.wrap_newspaper(web_page) 
        
        page.text = parser.text.strip()

        tree = web_page.lxml_tree()
        
        if len(page.text) == 0:
            for el in tree.xpath('//div[@itemprop="articleBody"]'):
                page.text = el.text_content().strip()

        page.title = page.get_title(tree, parser)
        page.date_published = page.get_date(tree)

        page.domain = urlparse(page.url_final).netloc
        page.source = source 

        return page

    def wrap_newspaper(self, web_page):
        parser = NewspaperArticle(url=web_page.final_url)
        parser.html = web_page.html
        parser.is_downloaded = True
        parser.parse()

        return parser

    def get_date(self, tree):
        dates = find_dates_tree(tree)

        if dates:
            return min(dates)
        else:
            return None

    def get_title(self, tree, parser):
        h1s = [(x.text_content().strip(), x.attrib) for x in tree.xpath('//h1')]
        
        headline = None
        for h1_headline, h1_attribs in h1s:
            if headline is None or len(headline) < len(h1_headline):
                headline = h1_headline

        for h1_headline, h1_attribs in h1s:
            if h1_attribs.get('itemprop', None) == 'headline':
                headline = h1_headline

        title = fix_title(parser.title)
        if headline and title != headline:
            title = headline

        return title

    def as_dict(self):
        d = {
            'url': self.url,
            'final_url': self.url_final,
            'title': self.title,
            'text': self.text,
            'date_published': self.date_published,
            'source': self.source,
            'domain': self.domain,
        }

        if self._id:
            d['_id'] = self._id

        return d

    def save(self):
        doc = self.as_dict()

        result = db_pages.insert_one(doc)
        self._id = result.inserted_id

        return self._id

    @classmethod
    def get(klass, page_id):
        doc = db_pages.find_one({'_id': page_id})

        if doc is not None:
            return klass(doc)
        else:
            return None

    @classmethod
    def get_url(klass, url):
        doc = db_pages.find_one({'url': url})

        if doc is not None:
            return klass(doc)
        else:
            return None
 
if __name__ == "__main__":
  url = sys.argv[1]

  page = Page(url)

  print page.as_dict()

