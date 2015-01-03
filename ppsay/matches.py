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

"""
Stupidly wrote this forgetting that it won't work.

Match ranges are based on tokens, not position in the raw string!

def annotate_text(matches, text, text_index):
    out = ""

    last = 0

    for match_type, match_id, (match_text_index, match_range, match_string) in matches:
        if text_index != match_text_index:
            continue

        out += text[last:match_range[0]]
        out += "<{}>".format(match_type)
        out += text[match_range[0]:match_range[1]]
        out += "</{}>".format(match_type)

        last = match_range[1]

    out += text[last:]

    return out"""

def add_matches(doc):
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


    for constituency in constituencies:
        match = find_matches([constituency['name']] + constituencies_names[cid(constituency['id'])],
                             text_tokens,
                             title_tokens)

        if match is not None:
            matches.append(('constituency', cid(constituency['id']), match))

    for candidate in get_candidates():
      names = [candidate['name']] + candidate['other_names']

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

      match = find_matches(names, text_tokens, title_tokens)

      if match is not None:
          matches.append(('candidate', candidate['id'], match))

    resolve_overlaps(matches)

    possible_party_matches = {}
    for match_type, match_id, _ in matches:
      if match_type == 'party':
          possible_party_matches[match_id] = {'id': parties[match_id]['id']}

    possible_constituency_matches = {}
    for match_type, match_id, _ in matches:
        if match_type == 'constituency':
            possible_constituency_matches[match_id] = {'id': cid(constituencies_index[match_id]['id'])}

    possible_candidate_matches = {}
    for match_type, match_id, _ in matches:
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
                         'id': candidate['id'],}

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
            candidate['state'] = 'confirmed'
            resolved_candidates.append(candidate)

    # Add candidates that the machine found.
    for candidate in doc['possible']['candidates']:
        candidate_state = 'unknown'

        if candidate['id'] in doc['user']['candidates']['confirm']:
            candidate_state = 'confirmed'
        elif candidate['id'] in doc['user']['candidates']['remove']:
            candidate_state = 'removed'

        candidate_ = get_candidate(candidate['id'])
        candidate_['state'] = candidate_state

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
        resolve_matches(doc)
        db.save(doc)

