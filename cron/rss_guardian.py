from ppsay.sources import get_source_if_matches
import feedparser

feed = feedparser.parse('http://feeds.theguardian.com/theguardian/politics/rss')

def clean_link(x):
    return x.split('#')[0]

for item in feed['items']:
    url = clean_link(item['guid'])
    print url
    result = get_source_if_matches(url, 'rss/guardian', 'approved')


