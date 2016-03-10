import sys
from datetime import datetime

from db import db_articles
from webcache import WebPage
from page import Page
from article import Article

def get_or_create_doc(pages):
    doc = db_articles.find_one({'keys': pages[0].url,})

    new = False

    if doc is None:
        article = Article.from_pages(pages) 
       
        new = True

    return new, article


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

        if web_page.is_local:
            result['skip'] = {
                'text': 'Already in cache',
            }
        else:
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
        new, article = get_or_create_doc([page])

    # If this has worked, process it unless we're skipping this or there's an error
    if 'error' not in result and 'skip' not in result and new:
        article.process()

        # Only save if it has matches
        has_matches = False

        for min_candidates, min_constituencies, min_parties in conditions:            
            if len(article.analysis['possible']['candidates']) >= min_candidates and \
               len(article.analysis['possible']['constituencies']) >= min_constituencies and \
               len(article.analysis['possible']['parties']) >= min_parties:
                has_matches = True

        if has_matches:
            print "    Matches found"
            result['success'] = {
                'text': 'Matches'
            }
            
            article.state = state

            try:
                article.save() 
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
        new, article = get_or_create_doc(page, source)
    except Article.FetchError, e:
        print "FAILED", e
        return None

    if new and article.pages is not None:
        article.process() 

        article.state = state
        article.save()

    return doc

