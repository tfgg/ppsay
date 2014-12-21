import json
from pymongo import MongoClient

candidates = json.load(open('parse_data/candidates.json'))

client = MongoClient()

db = client.news.articles

docs = db.find()

for doc in docs:
  if doc['page'] is None:
    continue

  text = doc['page']['text']
  title = doc['page']['title']

  possible_candidate_matches = {}

  for id, candidate in candidates.items():
    if candidate['name'] in text or candidate['name'] in title:
      possible_candidate_matches[id] = candidate

  print doc['key']
  doc['possible_candidate_matches'] = possible_candidate_matches

  db.save(doc)

