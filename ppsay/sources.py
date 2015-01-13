from pymongo import MongoClient
from urlparse import urlparse
from domains import domain_whitelist, add_domain
from tasks import task_get_page
from dates import add_date
from matches import add_matches, resolve_matches

client = MongoClient()

db_sources = client.news.sources
db_articles = client.news.articles

def add_source_whitelist(source_url, source):
    source_url_parsed = urlparse(source_url)
    
    if source_url_parsed.netloc in domain_whitelist:
        article_doc = get_source(source_url, source)

        return article_doc
    else:
        return None

def add_source(source_url, source):
    print source_url

    source_doc = db_sources.find_one({'url': source_url})

    if source_doc is None:
        source_url_parsed = urlparse(source_url)

        source_doc = {'url': source_url,
                      'source': source,
                      'domain': source_url_parsed.netloc}

        source_doc['_id'] = db_sources.save(source_doc)

    if source_doc['domain'] in domain_whitelist:
        article_doc = get_source(source_doc)
    else:
        article_doc = None

    if article_doc is not None:
        source_doc['article_id'] = article_doc['_id']
    else:
        source_doc['article_id'] = None

    db_sources.save(source_doc)

    return source_doc, article_doc

def get_source(source_url, source):
    doc = task_get_page(source_url, source)

    if doc['page'] is not None:
        try:
            add_date(doc)
        except ValueError: # ignore date errors for now
            pass

        add_domain(doc)
        add_matches(doc)

        resolve_matches(doc)

        doc['_id'] = db_articles.save(doc)

    return doc

