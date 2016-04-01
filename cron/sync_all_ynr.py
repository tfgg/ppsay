import os
import pickle
import re
import sys
import requests
import json
from collections import Counter
from pymongo import MongoClient
from urlparse import urlparse

from ppsay.importers import ynmp
from ppsay.db import db_articles, db_candidates

#if os.path.isfile('cache.pickle'):
#    cache = pickle.load(open('cache.pickle'))
#else:
cache = {}

def get_cache(url):
    if url not in cache:
        print "Not in cache", url
        cache[url] = requests.get(url,verify=False).json()
        #pickle.dump(cache, open('cache.pickle', 'w+'))
        
    return cache[url]

client = MongoClient()

url = "https://candidates.democracyclub.org.uk/api/v0.9/persons/?page_size=200"

all_ids = {
    candidate['id'] for candidate in db_candidates.find()
}
found_ids = set()

while True:
    print "Getting page"
    resp = get_cache(url)

    print "Updating candidates"
    for i, person in enumerate(resp['results']):
        print i,

        rtn = ynmp.save_person(person)

        if rtn:
            found_ids.add(rtn['id'])

    print

    if resp['next']:
        url = resp['next']
    else:
        break

print "Finding deleted candidates"
missing_ids = all_ids - found_ids

print len(missing_ids)
print missing_ids

for person_id in all_ids:
    candidate_doc = db_candidates.find_one({'id': person_id})

    if person_id not in missing_ids and candidate_doc.get('deleted', False):
        print u"  UNDELETING {name:} ({id:})".format(**candidate_doc)
        candidate_doc['deleted'] = False
        db_candidates.save(candidate_doc)
    elif person_id in missing_ids:
        print u"  {name:} ({id:}) deleted".format(**candidate_doc)
        candidate_doc['deleted'] = True
        db_candidates.save(candidate_doc)

