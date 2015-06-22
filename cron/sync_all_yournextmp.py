import re
import sys
import requests
import json
from collections import Counter
from pymongo import MongoClient
from urlparse import urlparse

from ppsay.sources import get_source_whitelist

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

url = "http://yournextmp.popit.mysociety.org/api/v0.1/export.json"

def save_person(person):
    if 'party_memberships' not in person:
        print person
        return

    id_schemes = {ident['scheme'] for ident in person['identifiers']}

    # Not entirely true, might have been in parliament previously but been turfed out?
    incumbent = 'uk.org.publicwhip' in id_schemes

    if person['party_memberships']:
        candidacies = {year: {'party': {'name': person['party_memberships'][year]['name'],
                                        'id': person['party_memberships'][year]['id'].split(':')[1],},
                              'constituency': {'name': person['standing_in'][year]['name'], 
                                               'id': person['standing_in'][year]['post_id'],},
                              'year': year,
                             } 
                       for year in person['party_memberships'] if
                         person['party_memberships'][year] is not None
                           and person['standing_in'][year] is not None}
    else:
        candidacies = {}

    candidate = {'name': person['name'].strip(),
                 'name_prefix': person.get('honorific_prefix', None),
                 'name_suffix': person.get('honorific_suffix', None),
                 'other_names': [x['name'] for x in person['other_names']],
                 'url': person['url'],
                 'id': person['id'],
                 'image': person.get('image', None),
                 'proxy_image': person.get('proxy_image', None),
                 'candidacies': candidacies,
                 'gender': person['gender'],
                 'incumbent': incumbent}

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

print "Downloading data"
export_data = requests.get(url).json()


print "Updating candidates"
for i, person in enumerate(export_data['persons']):
    print i, 
    save_person(person)
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

