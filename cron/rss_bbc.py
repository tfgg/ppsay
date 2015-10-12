import sys
from ppsay.feed import Feed

class BBCFeed(Feed):
    feed_urls = ['http://feeds.bbci.co.uk/news/politics/rss.xml']
    source = 'rss/bbc'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = BBCFeed(fresh)
    feed.fetch()

