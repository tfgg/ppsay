import sys
from ppsay.feed import Feed

class LibdemVoiceFeed(Feed):
    feed_urls = ['http://www.libdemvoice.org/feed']
    source = 'rss/libdem_voice'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = LibdemVoiceFeed(fresh)
    feed.fetch()

