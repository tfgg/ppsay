import requests
from lxml.html import parse
import sys

url1 = "http://surname.sofeminine.co.uk/w/surnames/most-common-surnames-in-great-britain.html"
url2 = "http://surname.sofeminine.co.uk/w/surnames/most-common-surnames-in-great-britain-{}.html"

def get_surnames(tree):
    return set(tree.xpath('//a[@class="nom"]/text()'))

names = get_surnames(parse(url1))

for i in range(2,58):
    print >>sys.stderr, i
    names.update(get_surnames(parse(url2.format(i))))

for name in names:
    print >>sys.stderr, name
    print name

