import sys
from ppsay.feed import Feed

class IndependentFeed(Feed):
    feed_urls = ['http://rss.feedsportal.com/c/266/f/3498/index.rss']
    source = 'rss/independent'
    link_key = 'id'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = IndependentFeed(fresh)
    feed.fetch()

