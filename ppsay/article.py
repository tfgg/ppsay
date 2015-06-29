import sys
import re

from webcache import WebPage
from newspaper import Article as NewspaperArticle
from ppsay.data import elections
from ppsay.dates import find_dates_tree

from db import db_articles

def fix_title(s):
    return re_title.sub("", s).strip()

re_title = re.compile("(\(From.*?\))")

class Article(object):
    class FetchError(Exception):
        pass

    def __init__(self, page):
        self.url = page.url

        if page.html is None:
            raise Article.FetchError(u"Could not fetch {}".format(self.url))

        self.url_final = page.final_url

        article = self.wrap_newspaper(page) 
        
        self.text = article.text

        tree = page.lxml_tree()

        self.get_title(tree, article)
        self.get_date(tree)

    def wrap_newspaper(self, page):
        article = NewspaperArticle(url=page.final_url)
        article.html = page.html
        article.is_downloaded = True
        article.parse()

        return article

    def get_date(self, tree):
        dates = find_dates_tree(tree)

        if dates:
            self.date_published = min(dates)
        else:
            self.date_published = None       

    def get_title(self, tree, article):
        h1s = [(x.text_content().strip(), x.attrib) for x in tree.xpath('//h1')]
        
        headline = None
        for h1_headline, h1_attribs in h1s:
            if headline is None or len(headline) < len(h1_headline):
                headline = h1_headline

        for h1_headline, h1_attribs in h1s:
            if h1_attribs.get('itemprop', None) == 'headline':
                headline = h1_headline

        self.title = fix_title(article.title)
        if headline and self.title != headline:
            self.title = headline

    def as_dict(self):
        return {'urls': [self.url],
                'final_urls': [self.url_final],
                'title': self.title,
                'text': self.text,
                'date_published': self.date_published,
                'parser': 'ArticleGeneric'}


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
        if article_doc['page']['date_published']:
            article_doc['order_date'] = article_doc['page']['date_published']
        else:
            article_doc['order_date'] = article_doc['time_added']
        
        if article_doc['order_date'] <= elections['ge2010']['date']:
            article_doc['election'] = 'ge2010'
        else:
            article_doc['election'] = 'ge2015'

    return article_docs

if __name__ == "__main__":
  url = sys.argv[1]

  page = Article(url)

  print page.as_dict()

