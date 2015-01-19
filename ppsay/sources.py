from pymongo import MongoClient
from urlparse import urlparse
from domains import domain_whitelist, add_domain
from tasks import task_get_page
from dates import add_date
from matches import add_matches, resolve_matches

client = MongoClient()

db_articles = client.news.articles

def get_source_whitelist(source_url, source):
    """
        Get a source and save it if the domain is in the whitelist.
    """

    source_url_parsed = urlparse(source_url)
    
    if source_url_parsed.netloc in domain_whitelist:
        article_doc = get_source(source_url, source, 'approved')

        return article_doc
    else:
        return None

def get_source_if_matches(source_url, source, state):
    """
        Get a source and save it if there are matches.
    """

    new, doc = task_get_page(source_url, source, False)
    
    if new and doc['page'] is not None:
        try:
            add_date(doc)
        except ValueError: # ignore date errors for now
            pass

        add_domain(doc)
        add_matches(doc)

        # Only save if it has matches
        if len(doc['possible']['candidates']) > 0 or \
           len(doc['possible']['constituencies']) > 0:

            resolve_matches(doc)
            doc['_id'] = db_articles.save(doc)

    return doc

def get_source(source_url, source, state):
    """
        Get a source and save it, no matter what.
    """

    new, doc = task_get_page(source_url, source)

    if new and doc['page'] is not None:
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

