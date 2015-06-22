import os.path
import yaml
from urlparse import urlparse

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def add_domain(doc):
    parsed_url = urlparse(doc['page']['final_urls'][0])

    return parsed_url.netloc

full_whitelist = yaml.load(open(os.path.join(BASE_PATH, 'data/domain_whitelist.yaml')))

domain_whitelist = [x for y in full_whitelist.values() for x in y]

if __name__ == "__main__":
    print domain_whitelist

