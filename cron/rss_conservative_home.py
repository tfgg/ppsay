import sys
from ppsay.feed import Feed

class ConservativeHomeFeed(Feed):
    feed_urls = ['http://www.conservativehome.com/feed']
    source = 'rss/conservative_home'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = ConservativeHomeFeed(fresh)
    feed.fetch()

