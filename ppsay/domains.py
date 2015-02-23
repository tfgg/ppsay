import os.path
import yaml
from urlparse import urlparse

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def add_domain(doc):
    parsed_url = urlparse(doc['keys'][0])
    doc['domain'] =  parsed_url.netloc

    return doc

#with open(os.path.join(BASE_PATH, 'data/domains_news.dat'), 'r') as f:
#    domain_whitelist = {line.split()[0] for line in f}

full_whitelist = yaml.load(open(os.path.join(BASE_PATH, 'data/domain_whitelist.yaml')))

domain_whitelist = [x for y in full_whitelist.values() for x in y]


if __name__ == "__main__":
    print domain_whitelist

