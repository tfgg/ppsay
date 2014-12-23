# -*- coding: utf-8 -*-
import json
from pymongo import MongoClient
from collections import Counter

constituencies = json.load(open('parse_data/constituencies.json'))

client = MongoClient()

db = client.news.articles

docs = db.find()

def score_match(constituency, text, title):
  names = [constituency]
  name_tokens = constituency.split()

  #if len(name_tokens) > 2:
  #  names.append(" ".join(name_tokens[1:]))

  #match_party = False

  #for party in candidate['parties']:
  #  if party['name'] in text or party['name'] in title:
  #    match_party = True

  for name in names:
    if name in text or name in title:
      return 1.0
    
  return 0.0
  
for doc in docs:
  if doc['page'] is None:
    continue
  
  print doc['key']

  text = doc['page']['text']
  title = doc['page']['title']

  possible_constituency_matches = {}

  for constituency in constituencies:
    score = score_match(constituency['name'], text, title)

    if score > 0.0:
      print constituency['name'], score

      constituency['score'] = score
      constituency['id_snip'] = constituency['id'].split(':')[1]
      possible_constituency_matches[constituency['id_snip']] = constituency

  doc['possible_constituency_matches'] = possible_constituency_matches.values()

  db.save(doc)

