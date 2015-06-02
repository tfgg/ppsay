import sys
import feedparser
import re
import lxml.html
import requests

from webcache import WebPage
#from goose import Goose
from newspaper import Article as NewspaperArticle
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from ppsay.data import elections
from ppsay.dates import find_dates_tree

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles

#g = Goose()

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def try_parse_date(x):
    try:
        return parse_date(x)
    except:
        return x

def fix_title(s):
    return re_title.sub("", s).strip()

re_title = re.compile("(\(From.*?\))")

class ArticleGeneric(object):
    class FetchError(Exception):
        pass

    def __init__(self, article_url):
        self.url = article_url

        page = WebPage(self.url, self.fetch)

        if page.html is None:
            raise ArticleGeneric.FetchError(u"Could not fetch {}".format(article_url))

        self.url_final = page.final_url

        article = NewspaperArticle(url=self.url_final)
        article.html = page.html
        article.is_downloaded = True
        article.parse()

        tree = lxml.html.fromstring(page.html)

        dates = find_dates_tree(tree)

        if dates:
            self.date_published = min(dates)
        else:
            self.date_published = None

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

        self.canonical_link = None #article.canonical_link
        self.text = article.text
        self.date_published = try_parse_date(article.publish_date)

    def as_dict(self):
        return {'urls': [self.url],
                'final_urls': [self.url_final],
                'title': self.title,
                'text': self.text,
                'date_published': self.date_published,
                'parser': 'ArticleGeneric'}

    @classmethod
    def fetch(self, url):
        print u"Getting fresh: {}".format(url)
        try:
            req = requests.get(url,
                               headers=headers,
                               timeout=10)

        except requests.exceptions.ConnectionError, e:
            print e
            req = None

        except requests.exceptions.ReadTimeout, e:
            print e
            req = None

        if req:
            # Sometimes the encoding isn't guessed correctly, update from HTML
            tree = lxml.html.fromstring(req.content)

            for charset in tree.xpath('//meta/@charset'):
                req.encoding = charset  

            #{'content': 'text/html; charset=utf-8', 'http-equiv': 'Content-Type'}   
            for content_type in tree.xpath('//meta'):
                if content_type.attrib.get('http-equiv', None) == 'Content-Type':
                    try:
                        charset = content_type.attrib['content'].split(';')[-1].split('=')[1].strip()
                        print "Fixing charset", charset
                        req.encoding = charset
                    except IndexError:
                        pass

 
        return req

def get_articles(person_ids, constituency_ids=None):
    if constituency_ids:
        article_docs = db_articles.find({'state': 'approved',
                                       '$or': [{'constituencies': {'$elemMatch': {'id': {'$in': constituency_ids}, 'state': {'$ne': 'removed'}}}},
                                               {'candidates': {'$elemMatch': {'id': {'$in': person_ids}, 'state': {'$nin': ['removed','removed_ml']}}}}]}) \
                                  .sort([["time_added", -1]])
    else:
        article_docs = db_articles.find({'state': 'approved',
                                         'candidates': {'$elemMatch': {'id': {'$in': person_ids}, 'state': {'$nin': ['removed','removed_ml']}}}}) \
                                  .sort([('time_added', -1)])


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

  page = ArticleGeneric(url)

  print page.as_dict()

