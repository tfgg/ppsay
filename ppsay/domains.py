import os.path

from urlparse import urlparse

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def add_domain(doc):
    parsed_url = urlparse(doc['key'])
    doc['domain'] =  parsed_url.netloc

    return doc

with open(os.path.join(BASE_PATH, '../parse_data/domains_news.dat'), 'r') as f:
    domain_whitelist = {line.split()[0] for line in f}
