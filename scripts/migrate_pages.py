from ppsay.page import Page
from ppsay.db import db_articles
from urlparse import urlparse

for doc in db_articles.find():
    if 'page' not in doc or doc['page'] is None:
        print "Skipping"
        continue

    page_ids = []

    for url, final_url in zip(doc['page']['urls'], doc['page']['final_urls']):
        print url, final_url

        d = doc['page']

        d['url'] = url
        d['final_url'] = final_url
        d['source'] = doc['source']
        d['domain'] = urlparse(final_url).netloc

        page = Page.get_url(d['url'])

        if page is None:
            print "Creating {}".format(d['url'])
            page = Page(d)
            page.save()
        else:
            print "Exists"

        page_ids.append(page._id)

    doc['pages'] = page_ids

    doc['analysis'] = {
        'matches': doc['matches'],
        'machine': doc['machine'],
        'possible': doc['possible'],
        'user': doc['user'],
        'final': {
            'candidates': doc['candidates'],
            'constituencies': doc['constituencies'],
        },
    }

    doc['output'] = {
        'quotes': doc['quotes'],
        'tags': doc['tags'],
        'tagged_html': doc['tagged_html'],
        'tag_clash': doc['tag_clash'],
    }

    del doc['matches']
    del doc['machine']
    del doc['possible']
    del doc['user']
    del doc['candidates']
    del doc['constituencies']

    del doc['quotes']
    del doc['tags']
    del doc['tagged_html']
    del doc['tag_clash']

    del doc['page']
    del doc['source']
    del doc['domain']
    
    #print doc

    db_articles.save(doc)

