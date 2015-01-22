# -*- coding: utf-8 -*-

import json
from bson import ObjectId
from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    parties,
    get_candidate,
    get_candidates
)

import re

sep_re = re.compile(u'[ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+')
 
def cid(s):
    return s.split(':')[-1]

def is_sublist(a, b):
    i = 0
    
    if a == []: return (0,0)

    while True:
        if i == len(b): return None

        if b[i:i + len(a)] == a:
            return (i, i + len(a))
        else:
            i = i + 1

token_re = re.compile(u'([^ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+)')
            
def get_tokens(s):
    tokens = []
    spans = []
    
    for match in token_re.finditer(s):
        tokens.append(match.groups()[0])
        spans.append(match.span())
        
    return tokens, spans

def find_matches(ss, *tokenss):
  for s in ss:
    tokens, _ = get_tokens(s.lower())

    for i, (s_tokens, s_spans) in enumerate(tokenss):

        sub = is_sublist(tokens, s_tokens)

        if sub is not None:
            yield (i, sub, s)

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

def make_quote(text, spans, sub):
  match_start = spans[max(sub[0]-10, 0)]
  match_end = spans[min(sub[1]+10, len(spans)-1)]

  quote = text[match_start[0]:match_end[1]]

  return quote

def add_matches(doc):
    texts = [doc['page']['text'],
             doc['page']['title']]

    texts_tokens = [get_tokens(text.lower()) for text in texts]

    matches = []

    for party_id, party in parties.items():
        names = [party['name']] + parties[party_id]['other_names']

        for match in find_matches(names, *texts_tokens):
          if match is not None:
            quote = make_quote(texts[match[0]], texts_tokens[match[0]][1], match[1]) 
            matches.append(('party', party_id, match, quote))


    for constituency in constituencies:
        names = [constituency['name']] + constituencies_names[cid(constituency['id'])]

        for match in find_matches(names, *texts_tokens):
          if match is not None:
            quote = make_quote(texts[match[0]], texts_tokens[match[0]][1], match[1]) 
            matches.append(('constituency', cid(constituency['id']), match, quote))

    def munge_names(names):
      for name in list(names):
          name_tokens = name.split()

          # If we have more than forename-surname, try middlename + surname
          # Catches, e.g. Máirtín Ó Muilleoir
          if len(name_tokens) > 2:
              names.append(" ".join(name_tokens[1:]))
              names.append(name_tokens[0] + " " + name_tokens[-1])

          # Macdonald -> Mcdonald
          if ' Mac' in name:
              names.append(name.replace('Mac', 'Mc'))


    for candidate in get_candidates():
      names = [candidate['name']] + candidate['other_names']

      munge_names(names)
      for match in find_matches(names, *texts_tokens):
        if match is not None:
          quote = make_quote(texts[match[0]], texts_tokens[match[0]][1], match[1]) 
          matches.append(('candidate', candidate['id'], match, quote))

    resolve_overlaps(matches)

    possible_party_matches = {}
    for match_type, match_id, _, quote in matches:
      if match_type == 'party':
          possible_party_matches[match_id] = {'id': parties[match_id]['id'], 'quote': quote}

    possible_constituency_matches = {}
    for match_type, match_id, _, quote in matches:
        if match_type == 'constituency':
            possible_constituency_matches[match_id] = {'id': cid(constituencies_index[match_id]['id']), 'quote': quote}

    possible_candidate_matches = {}
    for match_type, match_id, _, quote in matches:
        if match_type == 'candidate':
            candidate = get_candidate(match_id)

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

            match_doc = {'match_party': party_match,
                         'match_constituency': constituency_match,
                         'running_2015': is_running_2015,
                         'score': score,
                         'id': candidate['id'],
                         'quote': quote,}

            possible_candidate_matches[candidate['id']] = match_doc

    doc['possible'] = {}
    doc['possible']['candidates'] = possible_candidate_matches.values()
    doc['possible']['constituencies'] = possible_constituency_matches.values()
    doc['possible']['parties'] = possible_party_matches.values()
   
    #doc['annotated'] = {'title': 
 
    if 'user' not in doc:
        doc['user'] = {}

    if 'candidates' not in doc['user']:
        doc['user']['candidates'] = {'confirm': [], 'remove': []}

    if 'constituencies' not in doc['user']:
        doc['user']['constituencies'] = {'confirm': [], 'remove': []}

    return doc

def resolve_candidates(doc):
    resolved_candidates = []

    # Add candidates that users have added that the machine didn't find.
    for candidate_id in doc['user']['candidates']['confirm']:
        if not any([candidate_id == candidate['id'] for candidate in doc['possible']['candidates']]):
            candidate = get_candidate(candidate_id)

            if 'deleted' not in candidate or not candidate['deleted']:
                candidate['state'] = 'confirmed'
                candidate['quote'] = None
                resolved_candidates.append(candidate)

    # Add candidates that the machine found.
    for candidate in doc['possible']['candidates']:
        candidate_state = 'unknown'

        if candidate['id'] in doc['user']['candidates']['confirm']:
            candidate_state = 'confirmed'
        elif candidate['id'] in doc['user']['candidates']['remove']:
            candidate_state = 'removed'

        candidate_ = get_candidate(candidate['id'])
        if 'deleted' not in candidate_ or not candidate_['deleted']:
            candidate_['state'] = candidate_state
            candidate_['quote'] = candidate['quote']
            resolved_candidates.append(candidate_)

    return resolved_candidates

def resolve_constituencies(doc):
    resolved_constituencies = []
    
 
    # Add constituencies that users have added that the machine didn't find.
    for constituency_id in doc['user']['constituencies']['confirm']:
        if not any([constituency_id == constituency['id'] for constituency in doc['possible']['constituencies']]):
            constituency = constituencies_index[constituency_id]
            constituency['state'] = 'confirmed'
            constituency['score'] = 1.5
            constituency['quite'] = None
            resolved_constituencies.append(constituency)

    # Add constituencies that the machine found.
    for constituency in doc['possible']['constituencies']:
        constituency_state = 'unknown'

        if constituency['id'] in doc['user']['constituencies']['confirm']:
            constituency_state = 'confirmed'
        elif constituency['id'] in doc['user']['constituencies']['remove']:
            constituency_state = 'removed'

        constituency_ = constituencies_index[constituency['id']]
        constituency_['id'] = cid(constituency_['id'])
        constituency_['state'] = constituency_state
        constituency_['quote'] = constituency['quote']
        constituency_['score'] = 1.0

        resolved_constituencies.append(constituency_)

    return resolved_constituencies

def resolve_matches(doc):
    """
        Generate the final description of the tags by combining the machine matched
        tags and the user contributed tags.
    """

    if 'possible' in doc:
        doc['candidates'] = resolve_candidates(doc)
        doc['constituencies'] = resolve_constituencies(doc) 

    return

if __name__ == "__main__":
    from pymongo import MongoClient

    client = MongoClient()
    db = client.news.articles

    for doc in db.find():
        print doc['key'], doc['_id']

        if doc['page'] is not None and doc['page']['text'] is not None:
            add_matches(doc)

        resolve_matches(doc)
        db.save(doc)

