import sys
import feedparser
import re
import lxml.html
import requests
from webcache import cache_get
from goose import Goose

g = Goose()

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

class ArticleGeneric(object):
  class FetchError(Exception):
    pass

  def __init__(self, article_url):
    self.url = article_url

    self.html = cache_get(self.url, self.fetch)

    if self.html is not None:
      try:
        self.article = g.extract(raw_html=self.html)
      except IOError, e:
        raise ArticleGeneric.FetchError("Goose exception: {}".format(str(e)))
    else:
      raise ArticleGeneric.FetchError("Could not fetch {}".format(article_url))

  @classmethod
  def fetch(self, url):
    print "Getting fresh: {}".format(url)
    try:
      req = requests.get(url,headers=headers,timeout=10)
    except requests.exceptions.ReadTimeout:
      req = None
    
    return req

  def as_dict(self):
    return {'url': self.url,
            'url_canonical': self.article.canonical_link,
            'title': self.article.title,
            'text': self.article.cleaned_text,
            'date_published': self.article.publish_date,
            'parser': 'ArticleGeneric'}

if __name__ == "__main__":
  url = sys.argv[1]

  page = ArticleGeneric(url)

  print page.as_dict()

