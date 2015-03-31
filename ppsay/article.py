import sys
import feedparser
import re
import lxml.html
import requests
from webcache import cache_get
from goose import Goose
from iso8601 import parse_date

g = Goose()

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def try_parse_date(x):
  try:
    return parse_date(x)
  except:
    return x

re_title = re.compile("(\(From.*?\))")

class ArticleGeneric(object):
  class FetchError(Exception):
    pass

  def __init__(self, article_url):
    self.url = article_url

    rtn = cache_get(self.url, self.fetch)
    if rtn is None:
      raise ArticleGeneric.FetchError(u"Could not fetch {}".format(article_url))


    self.html, self.url_final = rtn

    try:
        try:
            self.article = g.extract(raw_html=self.html)
        except ValueError, e:
            raise ArticleGeneric.FetchError("Stupid unicode error, probably: {}".format(str(e)))
    except IOError, e:
        raise ArticleGeneric.FetchError("Goose exception: {}".format(str(e)))

  @classmethod
  def fetch(self, url):
    print u"Getting fresh: {}".format(url)
    try:
      req = requests.get(url,headers=headers,timeout=10)
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

  def as_dict(self):
    def fix_title(s):
        return re_title.sub("", s).strip()

    tree = lxml.html.fromstring(self.html)

    h1s = [(x.text_content().strip(), x.attrib) for x in tree.xpath('//h1')]
        
    headline = None
    for h1_headline, h1_attribs in h1s:
        if headline is None or len(headline) < len(h1_headline):
            headline = h1_headline

    for h1_headline, h1_attribs in h1s:
        if h1_attribs.get('itemprop', None) == 'headline':
            headline = h1_headline

    title = fix_title(self.article.title)
    if headline and title != headline:
        title = headline

    return {'urls': [self.url],
            'final_urls': [self.url_final],
            'url_canonical': self.article.canonical_link,
            'title': fix_title(self.article.title),
            'text': self.article.cleaned_text,
            'date_published': try_parse_date(self.article.publish_date),
            'parser': 'ArticleGeneric'}

if __name__ == "__main__":
  url = sys.argv[1]

  page = ArticleGeneric(url)

  print page.as_dict()

