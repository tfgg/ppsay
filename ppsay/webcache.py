from datetime import datetime
from pymongo import MongoClient

client = MongoClient()
db = client.news.web_cache

def cache_get(url, callback):
  doc = db.find_one({'url': url})

  if doc is None:
    resp = callback(url)

    if resp is not None:
      doc = {'html': resp.text,
             'headers_server': dict(resp.headers),
             'url_final': resp.url,
             'time_fetched': datetime.now(),
             'url': url,}

      db.save(doc)
    else:
      return None

  html = doc['html']

  return html

