import re
import sys
import requests
import json
from collections import Counter
from pymongo import MongoClient
from urlparse import urlparse

from ppsay.importers import ynmp
from ppsay.sources import get_source_whitelist
from ppsay.db import db_articles, db_candidates

client = MongoClient()

url = "http://yournextmp.popit.mysociety.org/api/v0.1/export.json"

url_regex = re.compile("(http|https)://([^\s]+)")

sources = []

all_ids = {
    candidate['id'] for candidate in db_candidates.find()
}
found_ids = set()

print "Downloading data"
export_data = requests.get(url).json()

print "Updating candidates"
for i, person in enumerate(export_data['persons']):
    print i, 
    ynmp.save_person(person)
    found_ids.add(person['id'])

    # Look for any new sources
    #if 'versions' in person:
    #    for version in person['versions']:
    #        sources.append(version['information_source'])
print

print "Finding deleted candidates"
missing_ids = all_ids - found_ids

for person_id in all_ids:
    candidate_doc = db_candidates.find_one({'id': person_id})

    if person_id not in missing_ids and candidate_doc.get('deleted', False):
        print "  UNDELETING {name:} ({id:})".format(**candidate_doc)
        candidate_doc['deleted'] = False
        db_candidates.save(candidate_doc)
    elif person_id in missing_ids:
        print "  {name:} ({id:}) deleted".format(**candidate_doc)
        candidate_doc['deleted'] = True
        db_candidates.save(candidate_doc)


print "Processing sources"

blocked_domains = Counter()

for source in sources:
    matches = url_regex.findall(source)
  
    for match in matches:
        source_url = "{}://{}".format(*match)

        doc = get_source_whitelist(source_url, 'ynmp-all')

        if doc is None:
            url_parsed = urlparse(source_url)
            blocked_domains[url_parsed.netloc] += 1

print "Statistics of blocked domains"
for domain, count in blocked_domains.most_common():
    print "  ", domain, count

