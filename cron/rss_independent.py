from ppsay.sources import get_source_if_matches
import feedparser

feed = feedparser.parse('http://rss.feedsportal.com/c/266/f/3498/index.rss')

def clean_link(x):
    return x.split('#')[0]

for item in feed['items']:
    url = clean_link(item['id'])
    print url
    get_source_if_matches(url, 'rss', 'approved')
