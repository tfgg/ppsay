import os.path
import yaml
from urlparse import urlparse
from db import db_domains

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def add_domain(doc):
    parsed_url = urlparse(doc['page']['final_urls'][0])

    return parsed_url.netloc

full_whitelist = yaml.load(open(os.path.join(BASE_PATH, 'data/domain_whitelist.yaml')))

domain_whitelist = [x for y in full_whitelist.values() for x in y]

def get_domain(domain):
    return db_domains.find_one({'domains': domain})

def add_domain(domain):
    domain_doc = {
        'domains': [domain],
        'name': domain,
        'categories': ['news'],
    }

    domain_doc['_id'] = db_domains.save(domain_doc)

    return domain_doc

if __name__ == "__main__":
    print domain_whitelist

