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
         'http://www.walesonline.co.uk/news/?service=rss',
         'http://www.accringtonobserver.co.uk/news/?service=rss',
         'http://www.dailypost.co.uk/news/?service=rss',
         'http://www.birminghammail.co.uk/news/?service=rss',
         'http://www.birminghampost.co.uk/news/?service=rss',
         'http://www.getbucks.co.uk/news/?service=rss',
         'http://www.chesterchronicle.co.uk/news/?service=rss',
         'http://www.crewechronicle.co.uk/news/?service=rss',
         'http://www.coventrytelegraph.net/news/?service=rss',
         'http://www.mirror.co.uk/all-about/politics?service=rss',
         'http://www.gazettelive.co.uk/news/?service=rss',
         'http://www.southportvisiter.co.uk/news/?service=rss',
         'http://www.gethampshire.co.uk/news/?service=rss',
         'http://www.getreading.co.uk/news/?service=rss',
         'http://www.getsurrey.co.uk/news/?service=rss',
         'http://www.getwestlondon.co.uk/news/?service=rss',
         'http://www.hinckleytimes.net/news/?service=rss',
         'http://www.examiner.co.uk/news/?service=rss',
         'http://www.liverpoolecho.co.uk/news/?service=rss',
         'http://www.loughboroughecho.net/news/?service=rss',
         'http://www.macclesfield-express.co.uk/news/?service=rss',
         'http://www.manchestereveningnews.co.uk/news/?service=rss',
         'http://www.southportvisiter.co.uk/news/?service=rss',
         'http://metro.co.uk/news/uk/feed/',
         'http://www.rossendalefreepress.co.uk/news/?service=rss',
         'http://www.runcornandwidnesweeklynews.co.uk/news/?service=rss',
         'http://www.solihullnews.net/news/?service=rss',
         'http://www.chroniclelive.co.uk/news/?service=rss',
         'http://www.thejournal.co.uk/news/?service=rss',
         'http://www.wharf.co.uk/news/?service=rss',
         'http://www.wirralnews.co.uk/news/?service=rss',
        ]

for feed_url in feeds:
    feed = feedparser.parse(feed_url)

    for item in feed['items']:
        url = item['link']
        get_source_if_matches(url,
                              'rss',
                              'approved',
                              [(1,0,1), # candidates, constituencies, parties
                               (3,0,0),
                               (2,0,1),],)

