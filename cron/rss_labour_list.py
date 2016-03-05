import sys
from ppsay.feed import Feed

class LabourListFeed(Feed):
    feed_urls = ['http://feeds.feedburner.com/LabourListLatestPosts?format=xml']
    source = 'rss/labour_list'

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = LabourListFeed(fresh)
    feed.fetch()

