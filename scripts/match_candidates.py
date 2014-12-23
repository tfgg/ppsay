# -*- coding: utf-8 -*-
import json
from pymongo import MongoClient
from collections import Counter

candidates = json.load(open('parse_data/candidates.json'))

inverse_full_name_count = Counter(candidate['name'] for candidate in candidates.values())
inverse_last_name_count = Counter(candidate['name'].split()[-1] for candidate in candidates.values())
inverse_first_name_count = Counter(candidate['name'].split()[0] for candidate in candidates.values())

client = MongoClient()

db = client.news.articles

docs = db.find()

def score_match(candidate, text, title):
  names = [candidate['name']]
  name_tokens = candidate['name'].split()

  if len(name_tokens) > 2:
    names.append(" ".join(name_tokens[1:]))

  match_party = False

  for party in candidate['parties']:
    if party['name'] in text or party['name'] in title:
      match_party = True

  for name in names:
    if name in text or name in title:
      if match_party:
        return 2.0
      else:
        return 1.0
    
  return 0.0
  
for doc in docs:
  if doc['page'] is None:
    continue
  
  print doc['key']

  text = doc['page']['text']
  title = doc['page']['title']

  possible_candidate_matches = {}

  for id, candidate in candidates.items():
    # If we have more than forename-surname, try middlename + surname
    # Catches, e.g. Máirtín Ó Muilleoir

    score = score_match(candidate, text, title)

    if score > 0.0:
      print candidate['name'], score

      candidate['score'] = score
      possible_candidate_matches[id] = candidate

  doc['possible_candidate_matches'] = possible_candidate_matches.values()

  db.save(doc)

