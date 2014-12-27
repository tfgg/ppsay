# -*- coding: utf-8 -*-
import re
import sys
import json

from bson import ObjectId
from pymongo import MongoClient
from collections import Counter

sep_re = re.compile(u'[ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+')

def is_sublist(a, b):
    i = 0
    
    if a == []: return True

    while True:
        if i == len(b): return False

        if b[i:i + len(a)] == a:
            return True
        else:
            i = i + 1

def find_matches(name, parties, text_tokens, title_tokens):
  names = [name]
  name_tokens = name.split()

  # If we have more than forename-surname, try middlename + surname
  # Catches, e.g. Máirtín Ó Muilleoir
  if len(name_tokens) > 2:
    names.append(" ".join(name_tokens[1:]))

  match_party = False

  for party in parties:
    party_tokens = sep_re.split(party)

    match_party = match_party or \
                  is_sublist(party_tokens, text_tokens) or \
                  is_sublist(party_tokens, title_tokens)

  for name in names:
    name_tokens = sep_re.split(name.lower())

    if is_sublist(name_tokens, text_tokens) or \
       is_sublist(name_tokens, title_tokens):
      if match_party:
        return 2.0
      else:
        return 1.0
    
  return 0.0

if __name__ == "__main__":
    candidates = json.load(open('parse_data/candidates.json'))
    client = MongoClient()
    db = client.news.articles

    if len(sys.argv) == 1:
        docs = db.find()
    else:
        doc_id = ObjectId(sys.argv[1])
        docs = db.find({'_id': doc_id})
      
    for doc in docs:
      if doc['page'] is None:
        continue
      
      print doc['key']

      text = doc['page']['text'].lower()
      title = doc['page']['title'].lower()
      text_tokens = sep_re.split(text)
      title_tokens = sep_re.split(title)

      possible_candidate_matches = {}

      for candidate in candidates:
        parties = [x['name'] for x in candidate['parties']]

        score = find_matches(candidate['name'], parties, text_tokens, title_tokens)

        if score > 0.0:
          print candidate['name'], score

          candidate['score'] = score
          possible_candidate_matches[candidate['id']] = candidate

      doc['possible_candidate_matches'] = possible_candidate_matches.values()

      db.save(doc)

