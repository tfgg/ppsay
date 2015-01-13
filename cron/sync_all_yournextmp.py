import re
import sys
import requests
import json
from pymongo import MongoClient
from urlparse import urlparse

from ppsay.tasks import task_get_page
from ppsay.dates import add_date
from ppsay.domains import add_domain, domain_whitelist
from ppsay.matches import add_matches, resolve_matches

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

url = "http://yournextmp.popit.mysociety.org/api/v0.1/persons?per_page=100"

if len(sys.argv) > 1:
    url = "http://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(sys.argv[1])

resp = requests.get(url).json()

def save_person(person):
    if person['party_memberships']:
        candidacies = {year: {'party': {'name': x['name'],
                                        'id': x['id'].split(':')[1],},
                              'constituency': {'name': person['standing_in'][year]['name'], 
                                               'id': person['standing_in'][year]['post_id'],}
                             } 
                       for year, x in person['party_memberships'].items() if x is not None}
    else:
        candidacies = {}

    candidate = {'name': person['name'].strip(),
                 'other_names': [x['name'] for x in person['other_names']],
                 'url': person['url'],
                 'id': person['id'],
                 'candidacies': candidacies,}

    candidate_doc = db_candidates.find_one({'id': person['id']})

    if candidate_doc is not None:
        candidate_doc.update(candidate)
    else:
        candidate_doc = candidate

    db_candidates.save(candidate_doc)

url_regex = re.compile("(http|https)://([^\s]+)")

sources = []

all_ids = {candidate['id'] for candidate in db_candidates.find()}
found_ids = set()

while True:
    if 'page' in resp:
        print "{} / {}".format(resp['page'], (resp['total'] / resp['per_page'] + 1))

    if type(resp['result']) is list:
        results = resp['result']
    else:
        results = [resp['result']]

    for i, person in enumerate(results):
        print i, 
        save_person(person)
        found_ids.add(person['id'])

        # Look for any new sources
        for version in person['versions']:
            sources.append(version['information_source'])

    print '\n',

    if 'next_url' in resp:
        resp = requests.get(resp['next_url']).json()
    else:
        break

print "Finding deleted candidates"
missing_ids = all_ids - found_ids

for missing_id in missing_ids:
    candidate_doc = db_candidates.find_one({'id': missing_id})

    print "{name:} ({id:}) deleted".format(**candidate_doc)
    candidate_doc['deleted'] = True

    db_candidates.save(candidate_doc)

print "Processing sources"

for source in sources:
    matches = url_regex.findall(source)
  
    for match in matches:
        source_url = "{}://{}".format(*match)
        url_parsed = urlparse(source_url)

        if url_parsed.netloc in domain_whitelist:
            doc = db_articles.find_one({'key': source_url})

            if doc is None:
                print "New source", source_url
                doc_id = task_get_page(source_url, "Source")

                doc = db_articles.find_one({'_id': doc_id})

                try:
                    add_date(doc)
                except ValueError: # ignore date errors for now
                    pass

                add_domain(doc)
                add_matches(doc)

                resolve_matches(doc)

                db_articles.save(doc)
        else:
            print "Not in whitelist:", source_url
