import sys
from ppsay.feed import Feed

class GuardianFeed(Feed):
    feed_urls = ['http://feeds.theguardian.com/theguardian/politics/rss']
    source = 'rss/guardian'
    link_key = 'guid'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = GuardianFeed(fresh)
    feed.fetch()

