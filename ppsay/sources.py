import sys
from urlparse import urlparse
from datetime import datetime

from domains import domain_whitelist, add_domain
from dates import add_date
from matches import add_matches, resolve_matches, add_quotes
from ml.assign import get_machine
from db import db_web_cache, db_articles
from article import Article
from webcache import WebPage

def get_or_create_doc(page, source):
    doc = db_articles.find_one({'keys': page.url})

    new = False

    if doc is None:
        article = Article(page)
        
        doc = {
            'page': article.as_dict(),
            'source': source,
            'time_added': datetime.now(),
            'keys': [page.url],
        }
       
        new = True

    return new, doc

def process_doc(doc):
    try:
        doc['page']['date_published'] = add_date(doc)
    except ValueError: # ignore date errors for now
        pass

    doc['domain'] = add_domain(doc)

    doc['matches'], doc['possible'] = add_matches([doc['page']['text'],
                                                   doc['page']['title'],])

    doc['quotes'], doc['tags'] = add_quotes(doc['matches'],
                                            [doc['page']['text'],
                                             doc['page']['title']])
    
    doc['machine'] = get_machine(doc)

    resolve_matches(doc)

    return

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

def get_source_if_matches(source_url, source, state, conditions=[(1, 0, 0)], fresh=False):
    """
        Get a source and save it if there are matches.

        min_candidates, min_constituencies, min_parties
    """

    page = WebPage(source_url)

    result = {
        'url': source_url,
        'source': source,
        'state': state
    }

    try:
        page.fetch()
    except WebPage.FailedToFetch, e:
        result['error'] = {
            'type': 'WebPage.FailedToFetch',
            'text': str(e),
        }
        print "FAILED", e
     
    if not fresh and 'error' not in result and page.is_local:
        print "Already in cache, skipping"
        result['skip'] = {
            'text': 'Already in cache'
        }
    else:
        print "Enforced fresh run"

    if 'error' not in result and 'skip' not in result:
        try:
            new, doc = get_or_create_doc(page, source)
        except Article.FetchError, e:
            print "FAILED", e
            result['error'] = {
                'type': 'Article.FetchError',
                'text': str(e),
            }

    if 'error' not in result and 'skip' not in result:
        if fresh or new and doc['page'] is not None:
            print "  New"

            process_doc(doc) 

            # Only save if it has matches
            has_matches = False

            for min_candidates, min_constituencies, min_parties in conditions:            
                if len(doc['possible']['candidates']) >= min_candidates and \
                   len(doc['possible']['constituencies']) >= min_constituencies and \
                   len(doc['possible']['parties']) >= min_parties:
                    has_matches = True

            if has_matches:
                print "    Matches"
                result['success'] = {
                    'text': 'Matches'
                }
                
                doc['state'] = state

                try:
                    doc['_id'] = db_articles.save(doc)
                except RuntimeError, e:
                    result['error'] = "RuntimeError: {}".format(str(e))
            else:
                print "    No matches"
                result['skip'] = {
                    'text': 'No matches'
                }
        else:
            result['skip'] = {
                'text': 'Not new'
            }
            print "  Not new"

    if 'error' in result:
        print >>sys.stderr, datetime.now(), result

    return result

def get_source(source_url, source, state):
    """
        Get a source and save it, no matter what.
    """
    
    page = WebPage(source_url)

    try:
        page.fetch()
    except WebPage.FailedToFetch, e:
        print "FAILED", e
        return None

    try:
        new, doc = get_or_create_doc(page, source)
    except Article.FetchError, e:
        print "FAILED", e
        return None

    if new and doc['page'] is not None:
        process_doc(doc) 

        doc['state'] = state
        doc['_id'] = db_articles.save(doc)

    return doc

