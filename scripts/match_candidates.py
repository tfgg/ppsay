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
    
    if a == []: return (0,0)

    while True:
        if i == len(b): return None

        if b[i:i + len(a)] == a:
            return (i, i + len(a))
        else:
            i = i + 1

def find_matches(ss, *tokenss):
  for s in ss:
    s_tokens = sep_re.split(s.lower())

    for i, tokens in enumerate(tokenss):
        sub = is_sublist(s_tokens, tokens)

        if sub is not None:
            return (i, sub, s)

  return None

def range_overlap(a, b):
    if a[1] <= b[0] or b[1] <= a[0]:
        return False
    else:
        return True

def resolve_overlaps(matches):
    overlap_found = True
    while overlap_found:
        overlap_found = False

        for i1, match1 in enumerate(matches):
            for i2, match2 in enumerate(matches):
                # Make sure we're not lookig at the same match object
                # Also only look for matches in same text (e.g. title<->title)
                if match1 != match2 and match1[1][0] == match2[1][0]:
                    if range_overlap(match1[2][1], match2[2][1]):
                        print "Overlap", match1, match2
                        size1 = match1[2][1][1] - match1[2][1][0]
                        size2 = match2[2][1][1] - match2[2][1][0]

                        if size1 > size2:
                            del matches[i2]
                        elif size2 > size1:
                            del matches[i1]
                        else:
                            #raise Exception("Overlaps of equal length")
                            # LA LA LA. DIDN'T HAPPEN.
                            continue

                        overlap_found = True
                        break

            if overlap_found:
                break

if __name__ == "__main__":
    candidates = json.load(open('parse_data/candidates.json'))
    parties = json.load(open('parse_data/parties.json'))
    constituencies = json.load(open('parse_data/constituencies.json'))
    constituencies_names = json.load(open('parse_data/constituencies_other_names.json'))

    candidate_index = {candidate['id']: candidate for candidate in candidates}
    constituency_index = {constituency['id'].split(":")[1]: constituency for constituency in constituencies}

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
      
      matches = []

      for party_id, party in parties.items():
          match = find_matches([party['name']] + parties[party_id]['other_names'],
                               text_tokens,
                               title_tokens)

          if match is not None:
              matches.append(('party', party_id, match))
     
      def cid(s):
        return s.split(':')[1]
 
      for constituency in constituencies:
          match = find_matches([constituency['name']] + constituencies_names[cid(constituency['id'])],
                               text_tokens,
                               title_tokens)

          if match is not None:
              matches.append(('constituency', cid(constituency['id']), match))

      for candidate in candidates:
          names = [candidate['name']] + candidate['other_names']

          for name in list(names):
              name_tokens = name.split()

              # If we have more than forename-surname, try middlename + surname
              # Catches, e.g. Máirtín Ó Muilleoir
              if len(name_tokens) > 2:
                  names.append(" ".join(name_tokens[1:]))
   
              # Macdonald -> Mcdonald
              if ' Mac' in name:
                  names.append(name.replace('Mac', 'Mc'))
 
          match = find_matches(names, text_tokens, title_tokens)

          if match is not None:
              matches.append(('candidate', candidate['id'], match))

      resolve_overlaps(matches)

      possible_party_matches = {}
      for match_type, match_id, _ in matches:
          if match_type == 'party':
              possible_party_matches[match_id] = parties[match_id]

      possible_constituency_matches = {}
      for match_type, match_id, _ in matches:
          if match_type == 'constituency':
              possible_constituency_matches[match_id] = constituency_index[match_id]

      possible_candidate_matches = {}
      for match_type, match_id, _ in matches:
        if match_type == 'candidate':
            candidate = candidate_index[match_id]

            party_match = False
            for _, candidacy in candidate['candidacies'].items():
                if candidacy['party']['id'] in possible_party_matches:
                    party_match = True
            
            constituency_match = False
            for _, candidacy in candidate['candidacies'].items():
                if candidacy['constituency']['id'] in possible_constituency_matches:
                    constituency_match = True

            is_running_2015 = '2015' in candidate['candidacies']

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
      doc['possible_constituency_matches'] = possible_constituency_matches.values()
      doc['possible_party_matches'] = possible_party_matches.values()

      db.save(doc)

