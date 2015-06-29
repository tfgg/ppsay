import bz2
import lxml.html
import requests

from bson.binary import Binary

from datetime import datetime
from db import db_web_cache

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}

def fetch(url):
    print u"Getting fresh: {}".format(url)
    try:
        req = requests.get(url,
                           headers=headers,
                           timeout=10)

    except requests.exceptions.ConnectionError, e:
        print e
        req = None

    except requests.exceptions.Timeout, e:
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

class WebPage(object):
    db = db_web_cache

    class NotInCache(Exception):
        pass

    class FailedToFetch(Exception):
        pass

    def __init__(self, url, fetcher=fetch):
        self.url = url
        self.fetcher = fetcher
        self.html = None
        self.final_url = None

        self.is_local = False
        self.is_remote = False

    def fetch(self, do_fresh=False):
        if self.html is None or do_fresh:
            try:
                self.fetch_local()
            except self.NotInCache, e:
                self.fetch_remote()
     
    def fetch_local(self):
        doc = self.db.find_one({'url': self.url})

        if doc is None:
            raise self.NotInCache(self.url)

        if 'html' in doc:
            self.html = doc['html']
        elif 'html_compressed' in doc:
            self.html = bz2.decompress(doc['html_compressed']).decode('utf-8')
 
        self.final_url = doc['url_final']

        self.is_local = True
        self.is_remote = False

    def fetch_remote(self):
        resp = self.fetcher(self.url)

        if resp is not None:
            self.html = resp.text
            self.final_url = resp.url
        
            self.is_local = False
            self.is_remote = True

            text_encoded = resp.text.encode('utf-8')
            text_compressed = Binary(bz2.compress(text_encoded))

            print "Compression ratio: {} -> {}".format(len(text_encoded), len(text_compressed))

            doc = {
                'html_compressed': text_compressed,
                'headers_server': dict(resp.headers),
                'url_final': resp.url,
                'time_fetched': datetime.now(),
                'url': self.url,
                'charset': resp.encoding,
            }

            doc_exists = self.db.find_one({'url': doc['url']})

            if doc_exists is not None:
                doc['_id'] = doc_exists['_id']
                
            self.db.save(doc)
            
        else:
            raise self.FailedToFetch(self.url)

    def lxml_tree(self):
        if self.html:
            return lxml.html.fromstring(self.html)
        else:
            return None

