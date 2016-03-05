import sys
import socket
from ppsay.feed import Feed

socket.setdefaulttimeout(10.0)

class NewsquestDayliesFeed(Feed):
    feed_urls = [
        'http://www.echo-news.co.uk/news/rss/',
        'http://www.oxfordmail.co.uk/news/rss/',
        'http://www.thepress.co.uk/news/rss/',
        'http://www.thenorthernecho.co.uk/news/rss/',
        'http://www.swindonadvertiser.co.uk/news/rss/',
        'http://www.theargus.co.uk/news/rss/',
        'http://www.bournemouthecho.co.uk/news/rss/',
        'http://www.dorsetecho.co.uk/news/rss/',
        'http://www.thetelegraphandargus.co.uk/news/rss/',
        'http://www.theboltonnews.co.uk/news/rss/',
        'http://www.heraldscotland.com/news/rss/',
        'http://www.eveningtimes.co.uk/news/rss/',
        'http://www.southwalesargus.co.uk/news/rss/',
        'http://www.dailyecho.co.uk/news/rss/',
        'http://www.lancashiretelegraph.co.uk/news/rss/',
        'http://www.sundayherald.com/news/rss/',
    ]
    source = 'rss/newsquest_daylies'
    
    def clean_link(self,x):
        return x.split('#')[0].split('?')[0]

if __name__ == "__main__":
    fresh = False
    if len(sys.argv) > 1:
        fresh = (sys.argv[1] == "fresh")

    feed = NewsquestDayliesFeed(fresh)
    feed.fetch()


