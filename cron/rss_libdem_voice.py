import sys
from ppsay.sources import get_source_if_matches
import feedparser

feed = feedparser.parse('http://www.libdemvoice.org/feed')

def clean_link(x):
    return x.split('#')[0]

fresh = False
if len(sys.argv) > 1:
    fresh = (sys.argv[1] == "fresh")

for item in feed['items']:
    url = clean_link(item['link'])
    print url
    get_source_if_matches(url, 'rss/libdem_voice', 'approved', fresh=fresh)

