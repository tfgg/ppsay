import sys
from ppsay.feed import Feed

class MiscFeed(Feed):
    feed_urls = [
        'http://50for15.com/feed/',
        'http://www.wellsjournal.co.uk/news.rss',
        'http://www.newstatesman.com/feeds/site_feed.rss',
    ]
    source = 'rss/misc'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = MiscFeed(fresh)
    feed.fetch()

