from urlparse import urlparse

def add_domain(doc):
    parsed_url = urlparse(doc['key'])
    print parsed_url.netloc
    doc['domain'] =  parsed_url.netloc

    return doc

