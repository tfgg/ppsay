import sys
from urlparse import urlparse

from pymongo import MongoClient
from ppsay.tasks import task_get_page
from ppsay.dates import add_date
from ppsay.domains import add_domain
from ppsay.matches import add_matches, resolve_matches

sources_domains_text = open('parse_data/sources_news.dat', 'r')
source_domains = []
for line in sources_domains_text:
  source_domains.append(line.split()[0])

client = MongoClient()
db_articles = client.news.articles

source = sys.argv[1]

url_parsed = urlparse(source)

if url_parsed.netloc in source_domains:
    doc_id = task_get_page(source, "User")

    print doc_id

    doc = db_articles.find_one({'_id': doc_id})

    add_date(doc)
    add_domain(doc)
    add_matches(doc)

    resolve_matches(doc)

    db_articles.save(doc)

else:
    print "Not a permitted source domain"

