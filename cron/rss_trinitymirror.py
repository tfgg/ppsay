import feedparser
from lxml.html import parse
from ppsay.sources import get_source_if_matches

url = "http://www.accringtonobserver.co.uk/all-about/politics"

tree = parse(url)

for url in tree.xpath('//div/h2/a/@href'):
    print url
#    get_source_if_matches(url, 'rss', 'approved')

feeds = ['http://www.dailyrecord.co.uk/news/politics/rss.xml',
         'http://www.gethampshire.co.uk/news/rss.xml',
        ]

for feed_url in feeds:
    feed = feedparser.parse(feed_url)

    for item in feed['items']:
        url = item['link']
        get_source_if_matches(url, 'rss', 'approved')

