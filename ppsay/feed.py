import feedparser
from ppsay.sources import get_source_if_matches

class Feed(object):
    feed_urls = None
    source = None
    match_condition = None
    link_key = 'link'

    def __init__(self, fresh):
        self.fresh = fresh

    def clean_link(self,x):
        return x.split('#')[0]

    def get_link(self,item):
        return item[self.link_key]

    def iter(self):
        for feed_url in self.feed_urls:
            feed = feedparser.parse(feed_url)

            for item in feed['items']:
                url = self.clean_link(self.get_link(item))
                yield url

    def __iter__(self):
        return self.iter()

    def fetch(self):
        if self.match_condition is None:
            for url in self.iter():
                result = get_source_if_matches(
                    url,
                    self.source,
                    'approved',
                    fresh=self.fresh,
                )
        else:            
            for url in self.iter():
                result = get_source_if_matches(
                    url,
                    self.source,
                    'approved',
                    self.match_condition,
                    fresh=self.fresh,
                )
 
