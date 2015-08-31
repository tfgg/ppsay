from ppsay.sources import get_source_if_matches
import feedparser

feeds = [('http://50for15.com/feed/', 'link'),
         ('http://www.wellsjournal.co.uk/news.rss', 'link'),
         ('http://www.newstatesman.com/feeds/topics/politics.rss', 'link')]

for url, key in feeds:
    feed = feedparser.parse(url)

    def clean_link(x):
        return x.split('#')[0]

    for item in feed['items']:
        url = clean_link(item[key])
        print url
        get_source_if_matches(url, 'rss/misc', 'approved')

