# -*- coding: utf-8 -*-

import sys
import json
from bson import ObjectId
from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    parties,
    get_candidate,
    get_candidates,
    squish_constituencies
)
from ss import Text

import re

sep_re = re.compile(u'[ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+')
 
def is_sublist(a, b):
    i = 0
    
    if a == []: yield (0,0)

    while i != len(b):

        if b[i:i + len(a)] == a:
            yield (i, i + len(a))

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
        for sub in is_sublist(tokens, s_tokens):
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
                if i1 != i2 and match1[2][0] == match2[2][0]:
                    if range_overlap(match1[2][1], match2[2][1]):
                        print "Overlap", match1, match2
                        size1 = match1[2][1][1] - match1[2][1][0]
                        size2 = match2[2][1][1] - match2[2][1][0]

                        if size1 > size2:
                            del matches[i2]
                            overlap_found = True
                            break
                        elif size2 > size1:
                            del matches[i1]
                            overlap_found = True
                            break
                        else:
                            print "Overlaps of equal length"

                            #if i1 > i2:
                            #    del matches[i1]
                            #    del matches[i2]
                            #else:
                            #    del matches[i2]
                            #    del matches[i1]

            if overlap_found:
                break


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


def add_tags(s, tags):
    tags = sorted(tags, key=lambda x: x[0])
   
    last = 0
    html = ""
    for (tag_start, tag_end), tag_begin, tag_fin in tags:
        if tag_start < last:
            print "Overlap"
            continue

        html += s[last:tag_start]
        html += tag_begin
        html += s[tag_start:tag_end]
        html += tag_fin
        last = tag_end
    html += s[last:]
    
    return html


def add_matches(doc):
    texts = [doc['page']['text'],
             doc['page']['title']]

    texts_tokens = [get_tokens(text.lower()) for text in texts]

    matches = []

    for party_id, party in parties.items():
        names = set([party['name']] + parties[party_id]['other_names'])

        for match in find_matches(names, *texts_tokens):
            if match is not None:
                matches.append(('party', party_id, match))


    for constituency in constituencies:
        names = set([constituency['name']] + constituencies_names[constituency['id']])

        for match in find_matches(names, *texts_tokens):
            if match is not None:
                matches.append(('constituency', constituency['id'], match))


    for candidate in get_candidates():
        names = [candidate['name']] + candidate['other_names']
        munge_names(names)
        names = set(names)

        for match in find_matches(names, *texts_tokens):
            if match is not None:
                matches.append(('candidate', candidate['id'], match))

    party_ids = {x[1] for x in matches if x[0] == 'party'}
    candidate_ids = {x[1] for x in matches if x[0] == 'candidate'}
    constituency_ids = {x[1] for x in matches if x[0] == 'constituency'}

    print "  Found {} parties".format(len(party_ids))
    print "  Found {} candidates".format(len(candidate_ids))
    print "  Found {} constituencies".format(len(constituency_ids))
    
    # Load in squish phrases for matched constituencies, e.g. Gordon Ramsay for Gordon.

    num_squish = 0
    for constituency_id in constituency_ids:
        if constituency_id in squish_constituencies:
            phrases = squish_constituencies[constituency_id]
            for match in find_matches(phrases, *texts_tokens):
                if match is not None:
                    matches.append(('squish', None, match))
                    num_squish += 1

    print "  Found {} squishes".format(num_squish)
    print "  Total {} matches".format(len(matches))

    for match in matches:
        print "   ", match[0], match[1], match[2]

    resolve_overlaps(matches)

    print "  Total {} matches remaining".format(len(matches))
    
    possible_party_matches = {}
    for match_type, match_id, _ in matches:
        if match_type == 'party':
            possible_party_matches[match_id] = {'id': parties[match_id]['id']}

    possible_constituency_matches = {}
    for match_type, match_id, _ in matches:
        if match_type == 'constituency':
            possible_constituency_matches[match_id] = {'id': constituencies_index[match_id]['id']}

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

    doc['matches'] = matches
    doc['possible'] = {}
    doc['possible']['candidates'] = possible_candidate_matches.values()
    doc['possible']['constituencies'] = possible_constituency_matches.values()
    #doc['possible']['parties'] = possible_party_matches.values()
 
    if 'user' not in doc:
        doc['user'] = {}

    if 'candidates' not in doc['user']:
        doc['user']['candidates'] = {'confirm': [], 'remove': []}

    if 'constituencies' not in doc['user']:
        doc['user']['constituencies'] = {'confirm': [], 'remove': []}

    return doc


def add_quotes(doc):
    texts = [doc['page']['text'],
             doc['page']['title']]

    texts_tokens = [get_tokens(text.lower()) for text in texts]

    parsed_texts = [Text(text) for text in texts]

    for parsed_text in parsed_texts:
        #if len(parsed_text.sample) not in parsed_text.end_of_sentences:
        #    parsed_text.end_of_sentences.append(len(parsed_text.sample))

        print parsed_text.markup()

    quotes = []

    for match_type, match_id, match in doc['matches']:
        sub = match[1]
        spans = texts_tokens[match[0]][1]

        wmatch_start = spans[max(sub[0], 0)][0]
        wmatch_end = spans[min(sub[1]-1, len(spans)-1)][1]

        for i, eos in enumerate(parsed_texts[0].end_of_sentences):
            if eos >= wmatch_start:
                if i != 0:
                    match_start = parsed_texts[0].end_of_sentences[i-1] + 1
                    match_end = eos
                else:
                    match_start = 0
                    match_end = parsed_texts[0].end_of_sentences[0] + 1
                break
        else:
            print "Fallthrough"
            match_start = 0
            match_end = len(texts[match[0]])

        quote_doc = {'constituency_ids': [],
                     #'party_ids': [],
                     'candidate_ids': [],
                     'quote_span': (match_start, match_end),
                     'match_text': match[0]}

        print match
        print quote_doc

        if match_type == 'candidate':
            quote_doc['candidate_ids'].append((match_id, wmatch_start, wmatch_end))
        #elif match_type == 'party':
        #    quote_doc['party_ids'].append((match_id, wmatch_start, wmatch_end))
        elif match_type == 'constituency':
            quote_doc['constituency_ids'].append((match_id, wmatch_start, wmatch_end))

        quotes.append(quote_doc)

        #print quote_doc

    similar_pairs = []
    for i, quote1 in enumerate(quotes):
        for j, quote2 in enumerate(quotes):
            if quote1['match_text'] == quote2['match_text'] and \
               range_overlap(quote1['quote_span'], quote2['quote_span']):
                similar_pairs.append((i,j))

    groups = []
    for similar_pair in similar_pairs:
        for group in groups:
            if similar_pair[0] in group or similar_pair[1] in group:
                group.add(similar_pair[0])
                group.add(similar_pair[1])
                break
        else:
            groups.append(set(similar_pair))

    merged_quotes = []
    for group in groups:
        quote = {'constituency_ids': list(set(sum([quotes[i]['constituency_ids'] for i in group], []))),
                 ##'party_ids': list(set(sum([quotes[i]['party_ids'] for i in group], []))),
                 'candidate_ids': list(set(sum([quotes[i]['candidate_ids'] for i in group], []))),
                 'quote_span': (min(quotes[i]['quote_span'][0] for i in group),
                                max(quotes[i]['quote_span'][1] for i in group),),
                 'match_text': quotes[i]['match_text'],}
 
        merged_quotes.append(quote)
    
    quotes = merged_quotes 

    for quote in quotes:
        print quote

    print "  Total {} quotes".format(len(quotes))
    
    doc['quotes'] = quotes

def resolve_candidates(doc):
    resolved_candidates = []

    # Add candidates that users have added that the machine didn't find.
    for candidate_id in doc['user']['candidates']['confirm']:
        if not any([candidate_id == candidate['id'] for candidate in doc['possible']['candidates']]):
            candidate = get_candidate(candidate_id)

            if 'deleted' not in candidate or not candidate['deleted']:
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
        if 'deleted' not in candidate_ or not candidate_['deleted']:
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
        constituency_['id'] = constituency_['id']
        constituency_['state'] = constituency_state
        constituency_['score'] = 1.0

        resolved_constituencies.append(constituency_)

    return resolved_constituencies


def resolve_quotes(doc):
    texts = [doc['page']['text'],
             doc['page']['title']]

    candidates = {candidate['id']: candidate for candidate in doc['candidates'] if candidate['state'] != 'removed'}
    constituencies = {constituency['id']: constituency for constituency in doc['constituencies'] if constituency['state'] != 'removed'}

    for quote_doc in doc['quotes']:
        # Grab info, only include if they're in the final resolvesd constituencies/candidates 
        quote_doc['candidates'] = [candidates[candidate_id[0]] for candidate_id in quote_doc['candidate_ids'] if candidate_id[0] in candidates]
        quote_doc['constituencies'] = [constituencies[constituency_id[0]] for constituency_id in quote_doc['constituency_ids'] if constituency_id[0] in constituencies]
        #quote['parties'] = [parties[party_id[0]] for party_id in quote['party_ids']]

        quote_text = texts[quote_doc['match_text']][quote_doc['quote_span'][0]:quote_doc['quote_span'][1]]
    
        quote_doc['text'] = quote_text

        offset = quote_doc['quote_span'][0]
       
        tags = [((s-offset, e-offset), "<a href='/articles/person/{0}' class='quote-candidate-highlight quote-candidate-{0}-highlight'>".format(id), "</a>") for id, s, e in quote_doc['candidate_ids'] if id in candidates]

        tags += [((s-offset, e-offset), "<a href='/articles/constituency/{0}' class='quote-constituency-highlight quote-constituency-{0}-highlight'>".format(id), "</a>") for id, s, e in quote_doc['constituency_ids'] if id in constituencies]
 
        quote_html = add_tags(quote_text, tags)
        quote_doc['tags'] = tags
        quote_doc['html'] = quote_html.strip()

def resolve_matches(doc):
    """
        Generate the final description of the tags by combining the machine matched
        tags and the user contributed tags.
    """

    if 'possible' in doc:
        doc['candidates'] = resolve_candidates(doc)
        doc['constituencies'] = resolve_constituencies(doc) 

    if 'quotes' in doc:
        resolve_quotes(doc)

    return

if __name__ == "__main__":
    from pymongo import MongoClient

    client = MongoClient()
    db = client.news.articles

    if len(sys.argv) == 1:
        docs = db.find() \
                 .sort([('time_added', -1)])
    else:
        docs = db.find({'_id': ObjectId(sys.argv[1])})

    for doc in docs:
        #if 'quotes' in doc:
        #    continue

        print doc['key'], doc['_id']

        if doc['page'] is not None and doc['page']['text'] is not None:
            add_matches(doc)
            add_quotes(doc)

        resolve_matches(doc)
        db.save(doc)

