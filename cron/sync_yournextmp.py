import sys
import requests
import json
from bson import ObjectId
from pymongo import MongoClient

client = MongoClient()

db_candidates = client.news.candidates

url = "http://yournextmp.popit.mysociety.org/api/v0.1/persons?per_page=100"

if len(sys.argv) > 1:
    url = "http://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(sys.argv[1])

print url
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

      # Look for any new sources
      #for version in membership['person_id']['versions']:
      #  print version['source']

    print '\n',

    if 'next_url' in resp:
        resp = requests.get(resp['next_url']).json()
    else:
        break

