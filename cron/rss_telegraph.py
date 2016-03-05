import sys
from ppsay.feed import Feed

class TelegraphFeed(Feed):
    feed_urls = ['http://www.telegraph.co.uk/news/politics/rss']
    source = 'rss/telegraph'
    link_key = 'guid'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = TelegraphFeed(fresh)
    feed.fetch()

