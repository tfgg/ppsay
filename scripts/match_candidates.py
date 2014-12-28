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

def find_matches(ss, *tokenss):
  for s in ss:
    s_tokens = sep_re.split(s.lower())

    for tokens in tokenss:
        if is_sublist(s_tokens, tokens):
            return True

  return False

if __name__ == "__main__":
    candidates = json.load(open('parse_data/candidates.json'))
    parties = json.load(open('parse_data/parties.json'))
    constituencies = json.load(open('parse_data/constituencies.json'))
    constituencies_names = json.load(open('parse_data/constituencies_other_names.json'))

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
      
      party_matches = {party_id: party['name']
                       for party_id, party in parties.items()
                       if find_matches([party['name']] + parties[party_id]['other_names'],
                                       text_tokens,
                                       title_tokens)}
     
      def cid(s):
        return s.split(':')[1]
 
      constituency_matches = {cid(constituency['id']): constituency['name']
                              for constituency in constituencies
                              if find_matches([constituency['name']] + constituencies_names[cid(constituency['id'])],
                                              text_tokens,
                                              title_tokens)}


      print party_matches
      print constituency_matches

      possible_candidate_matches = {}

      for candidate in candidates:
        party_match = False
        for _, candidacy in candidate['candidacies'].items():
            if candidacy['party']['id'] in party_matches:
                party_match = True
        
        constituency_match = False
        for _, candidacy in candidate['candidacies'].items():
            if candidacy['constituency']['id'] in constituency_matches:
                constituency_match = True
    
        names = [candidate['name']] + candidate['other_names']

        for name in list(names):
            name_tokens = name.split()

            # If we have more than forename-surname, try middlename + surname
            # Catches, e.g. Máirtín Ó Muilleoir
            if len(name_tokens) > 2:
                names.append(" ".join(name_tokens[1:]))
    
        name_match = find_matches(names, text_tokens, title_tokens)

        is_running_2015 = '2015' in candidate['candidacies']

        # Name has to match
        if name_match:
            score = 0.0

            if party_match:
                score += 0.5

            if constituency_match:
                score += 0.5

            if is_running_2015:
                score += 0.5

            print candidate['name'], score, party_match, constituency_match, is_running_2015

            candidate['match_party'] = party_match
            candidate['match_constituency'] = constituency_match
            candidate['score'] = score
            possible_candidate_matches[candidate['id']] = candidate

      doc['possible_candidate_matches'] = possible_candidate_matches.values()

      db.save(doc)

