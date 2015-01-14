from pymongo import MongoClient
from urlparse import urlparse
from domains import domain_whitelist, add_domain
from tasks import task_get_page
from dates import add_date
from matches import add_matches, resolve_matches

client = MongoClient()

db_articles = client.news.articles

def get_source_whitelist(source_url, source):
    source_url_parsed = urlparse(source_url)
    
    if source_url_parsed.netloc in domain_whitelist:
        article_doc = get_source(source_url, source, 'approved')

        return article_doc
    else:
        return None

def get_source(source_url, source, state):
    doc = task_get_page(source_url, source)

    if doc['page'] is not None:
        try:
            add_date(doc)
        except ValueError: # ignore date errors for now
            pass

        add_domain(doc)
        add_matches(doc)

        resolve_matches(doc)

        doc['state'] = state

        doc['_id'] = db_articles.save(doc)

    return doc

