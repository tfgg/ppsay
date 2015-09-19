import json
from ppsay.data import parties
from pymongo import MongoClient

client = MongoClient()

people = client.news.candidates

for person in people.find():
    for _, candidacy in person['candidacies'].items():
        party = candidacy['party']

        if party['id'] not in parties:
            
            parties[party['id']] = {
                'name': party['name'],
                'id': party['id'],
                'other_names': [],
            }
        else:
            if parties[party['id']]['name'] != party['name'] and 'TFGG' not in parties[party['id']]['name']:
                parties[party['id']]['other_names'].append(parties[party['id']]['name'])
                parties[party['id']]['name'] = party['name']

print json.dumps(parties, indent=4, sort_keys=True)

