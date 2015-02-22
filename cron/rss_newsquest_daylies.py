from ppsay.sources import get_source_if_matches
import socket
import feedparser

socket.setdefaulttimeout(10.0)

daylies = ['http://www.echo-news.co.uk',
 'http://www.oxfordmail.co.uk',
 'http://www.thepress.co.uk',
 'http://www.thenorthernecho.co.uk',
 'http://www.swindonadvertiser.co.uk',
 'http://www.theargus.co.uk',
 'http://www.bournemouthecho.co.uk',
 'http://www.dorsetecho.co.uk',
 'http://www.thetelegraphandargus.co.uk',
 'http://www.theboltonnews.co.uk',
 'http://www.heraldscotland.com',
 'http://www.eveningtimes.co.uk',
 'http://www.southwalesargus.co.uk',
 'http://www.dailyecho.co.uk',
 'http://www.lancashiretelegraph.co.uk']

sundays = ['http://www.sundayherald.com']

for url in daylies:
    print url
    feed = feedparser.parse(url + '/news/rss/')

    def clean_link(x):
        return x.split('#')[0].split('?')[0]

    for item in feed['items']:
        url = clean_link(item['link'])
        print url
        get_source_if_matches(url, 'rss', 'approved', min_candidates=1, min_parties=1, min_constituencies=0)


