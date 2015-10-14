import sys
from urlparse import urlparse
from datetime import datetime

from domains import domain_whitelist
from dates import add_date
from matches import add_matches, resolve_matches, add_quotes
from ml.assign import get_machine
from db import db_web_cache, db_articles, db_pages
from webcache import WebPage
from page import Page

def get_or_create_doc(pages):
    doc = db_articles.find_one({'keys': pages[0].url,})

    new = False

    if doc is None:
        doc = {
            'pages': [page._id for page in pages],
            'time_added': datetime.now(),
            'keys': [page.url for page in pages],
            'analysis': {},
            'output': {},
        }
       
        new = True

    return new, doc

def process_doc(doc):
    page = Page.get(doc['pages'][0])

    texts = [page.text, page.title,]

    if 'analysis' not in doc:
        doc['analysis'] = {}

    if 'output' not in doc:
        doc['output'] = {}

    doc['analysis']['matches'], doc['analysis']['possible'] = add_matches(texts)

    doc['output']['quotes'], doc['output']['tags'] = add_quotes(doc['analysis']['matches'], texts)
    
    doc['analysis']['machine'] = get_machine(doc)

    resolve_matches(texts, doc)

    return


def get_source_if_matches(source_url, source, state, conditions=[(1, 0, 0)], fresh=False):
    """
        Get a source and save it if there are matches.

        min_candidates, min_constituencies, min_parties
    """
    
    result = {
        'url': source_url,
        'source': source,
        'state': state
    }

    # First, get the parsed page object 
    page = Page.get_url(source_url)

    if page is not None:
        print "Page already exists."

        if not fresh:
            result['skip'] = {
                'text': 'Page already exists.'
            }

    else:
        print "Page doesn't exist"

        web_page = WebPage(source_url)

        try:
            web_page.fetch()
        except WebPage.FailedToFetch, e:
            result['error'] = {
                'type': 'WebPage.FailedToFetch',
                'text': str(e),
            }

        try:
            page = Page.from_web_page(web_page, source)
            page.save()
        except Page.FetchError, e:
            print "FAILED", e
            result['error'] = {
                'type': 'Page.FetchError',
                'text': str(e),
            }

    # Next, using the page object, get the article object or create a new one
    if 'error' not in result and 'skip' not in result:
        new, doc = get_or_create_doc([page])

    # If this has worked, process it unless we're skipping this or there's an error
    if 'error' not in result and 'skip' not in result and new:
        process_doc(doc) 

        # Only save if it has matches
        has_matches = False

        for min_candidates, min_constituencies, min_parties in conditions:            
            if len(doc['analysis']['possible']['candidates']) >= min_candidates and \
               len(doc['analysis']['possible']['constituencies']) >= min_constituencies and \
               len(doc['analysis']['possible']['parties']) >= min_parties:
                has_matches = True

        if has_matches:
            print "    Matches found"
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

