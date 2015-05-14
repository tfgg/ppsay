import bz2
from bson.binary import Binary

from datetime import datetime
from pymongo import MongoClient

client = MongoClient()

class WebPage(object):
    db = client.news.web_cache

    def __init__(self, url, fetcher):
        self.url = url
        self.fetcher = fetcher
        self.html = None
        self.final_url = None

        self.fetch()

    def fetch(self):
        success = self.fetch_local()

        if not success:
            success = self.fetch_remote()

    def fetch_local(self):
        doc = self.db.find_one({'url': self.url})

        if doc is None:
            return False

        if 'html' in doc:
            self.html = doc['html']
        elif 'html_compressed' in doc:
            self.html = bz2.decompress(doc['html_compressed']).decode('utf-8')
 
        self.final_url = doc['url_final']

        return True

    def fetch_remote(self):
        resp = self.fetcher(self.url)

        if resp is not None:
          self.html = resp.text
          self.final_url = resp.url

          text_encoded = resp.text.encode('utf-8')
          text_compressed = Binary(bz2.compress(text_encoded))

          print "Compression ratio: {} -> {}".format(len(text_encoded), len(text_compressed))

          doc = {'html_compressed': text_compressed,
                 'headers_server': dict(resp.headers),
                 'url_final': resp.url,
                 'time_fetched': datetime.now(),
                 'url': self.url,
                 'charset': resp.encoding}

          self.db.save(doc)

          return True
        else:
          return False

