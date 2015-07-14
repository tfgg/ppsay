# -*- coding: utf-8 -*-

import sys
import json
from itertools import combinations

from bson import ObjectId
from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    parties,
    get_candidate,
    get_candidates,
    squish_constituencies,
)
from ml.assign import get_machine
from ss import Text

import re

from text import (
    is_sublist,
    get_tokens,
    find_matches,
    range_overlap,
    add_tags,
)

from itertools import chain
from collections import namedtuple

from ppsay.match_lookup import get_ngrams, index, munge_names

MatchEntity = namedtuple('MatchEntity', ['type', 'id', 'match']) 
Matches = namedtuple('Matches', ['matches', 'possible'])
MatchQuotes = namedtuple('MatchQuotes', ['quotes', 'tags'])

def find_overlaps(matches):
    for i, match1 in enumerate(matches):
        for j, match2 in enumerate(matches[i+1:]):
            if match2.match.range[0] >= match1.match.range[1]:
                break

            if match2.match.range[0] < match1.match.range[1] and match2.match.range[1] > match1.match.range[0]:
                yield i, j+i+1


def resolve_overlaps(matches, verbose=False):
    matches = sorted(matches, key=lambda match: match.match.range[0])
    
    remove = set()
    for i, j in find_overlaps(matches):
        match1 = matches[i]
        match2 = matches[j]

        size1 = match1.match.range[1] - match1.match.range[0]
        size2 = match2.match.range[1] - match2.match.range[0]
        
        if i in remove or j in remove:
            continue
        
        if match1.type.endswith("_extra") and not match2.type.endswith("_extra"):
            remove.add(i)
                        
        elif match2.type.endswith("_extra") and not match1.type.endswith("_extra"):
            remove.add(j)

        elif size1 > size2:
            remove.add(j)

        elif size1 < size2:
            remove.add(i)

        else:
            if verbose:
                print "Same", i, j
            
    for i, match in enumerate(matches):
        if i not in remove:
            yield match


def generate_extra_names(names, gender=None):
    """
        Make extra (non-primary) names to match someone.

        These are only used when there's a primary match.
    """
    extra_names = []

    # Try to only match gender appropriate titles
    titles = {'Dr', 'Cllr', 'Sir', 'Prof'}

    if gender and gender.lower() == 'male':
        titles |= {'Mr'}
    elif gender and gender.lower() == 'female':
        titles |= {'Mrs', 'Miss', 'Ms'}
    else:
        titles |= {'Mr', 'Mrs', 'Miss', 'Ms'}

    blacklist = {'pub', 'the', 'landlord', 'pub landlord', 'will'}

    for name in names:
        name_bits = name.split()

        extra_names.append(name_bits[0].lower())
        extra_names.append(name_bits[-1].lower())
        extra_names.append(" ".join(name_bits[-2:-1]).lower())

        for title in titles:
            extra_names.append(u"{} {}".format(title, name).lower())
            extra_names.append(u"{} {}".format(title, name_bits[-1]).lower())

        extra_names.append(u"Sir {}".format(name_bits[0]).lower())
    
    return set(extra_names) - blacklist


def add_matches(texts, verbose=False):
    #texts = [doc['page']['text'],
    #         doc['page']['title']]

    texts_tokens = [get_tokens(text.lower()) for text in texts]

    # Pre-screen with an n-gram match
    ngrams = chain(*[get_ngrams(text_tokens.tokens, n) for n in range(1,4) for text_tokens in texts_tokens])

    poss_matches = set()
    for ngram in ngrams:
        if ngram in index:
            poss_matches |= set(index[ngram])

    match_entities = []

    # Take candidate matches and refine match
    for obj_type, obj_index in poss_matches:
        extra_names = []

        if obj_type == 'party':
            party = parties[obj_index]
            names = set([party['name']] + parties[obj_index]['other_names'])

        elif obj_type == 'constituency':
            constituency = constituencies_index[obj_index]
            names = set([constituency['name']] + constituencies_names[constituency['id']])

        elif obj_type == 'candidate':
            candidate = get_candidate(obj_index)
            names = [candidate['name']] + candidate['other_names']
            extra_names = generate_extra_names(names, candidate.get('gender', None))
            munge_names(names, candidate['incumbent'], candidate['name_prefix'])
            names = set(names)

        have_matches = False
        for match in find_matches(names, *texts_tokens):
            match_entities.append(MatchEntity(type=obj_type, id=obj_index, match=match))
            have_matches = True

        # If we have some definite matches, do some looser matches, e.g. Tim Green -> Mr Green
        if have_matches:
            for match in find_matches(extra_names, *texts_tokens):
                match_entities.append(MatchEntity(type=obj_type + "_extra", id=obj_index, match=match))
            

    party_ids = {x[1] for x in match_entities if x.type == 'party'}
    candidate_ids = {x[1] for x in match_entities if x.type == 'candidate'}
    constituency_ids = {x[1] for x in match_entities if x.type == 'constituency'}

    print "  Found {} parties".format(len(party_ids))
    print "  Found {} candidates".format(len(candidate_ids))
    print "  Found {} constituencies".format(len(constituency_ids))
    
    # Load in squish phrases for matched constituencies, e.g. Gordon Ramsay for Gordon.

    num_squish = 0
    for constituency_id in constituency_ids:
        if constituency_id in squish_constituencies:
            phrases = squish_constituencies[constituency_id]
            for match in find_matches(phrases, *texts_tokens):
                match_entities.append(MatchEntity(type='squish', id=None, match=match))
                num_squish += 1

    # Fixes complaint about https://www.electionmentions.com/article/553ab95f238f31772f962b5d
    extra_squishes = ['Ian Smart']
    for match in find_matches(extra_squishes, *texts_tokens):
        match_entities.append(MatchEntity(type='squish', id=None, match=match))
        num_squish += 1


    print "  Found {} squishes".format(num_squish)
    print "  Total {} matches".format(len(match_entities))

    if verbose:
        for match_entity in match_entities:
            print "   ", match_entity

    match_entities = list(resolve_overlaps(match_entities, verbose))

    print "  Total {} matches remaining".format(len(match_entities))
    
    possible_party_matches = {}
    for match_entity in match_entities:
        if match_entity.type == 'party':
            possible_party_matches[match_entity.id] = {'id': parties[match_entity.id]['id']}

    possible_constituency_matches = {}
    for match_entity in match_entities:
        if match_entity.type == 'constituency':
            possible_constituency_matches[match_entity.id] = {'id': constituencies_index[match_entity.id]['id']}

    possible_candidate_matches = {}
    for match_entity in match_entities:
        if match_entity.type == 'candidate':
            candidate = get_candidate(match_entity.id)

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

    # Remove extra matches which no longer have a parent match
    def filter_extra(match_entity):
        if match_entity.type == 'candidate_extra':
            if match_entity.id not in possible_candidate_matches:
                print match_entity, "not got parent"
                return False
        return True


    possible = {}
    possible['candidates'] = possible_candidate_matches.values()
    possible['constituencies'] = possible_constituency_matches.values()
    possible['parties'] = possible_party_matches.values()
    
    return Matches(matches=filter(filter_extra, match_entities),
                   possible=possible)

MatchTag = namedtuple('MatchTag', ['start', 'end', 'type', 'id', 'source']) 

def add_quotes(matches, texts):
    texts_tokens = [get_tokens(text.lower()) for text in texts]
    parsed_texts = [Text(text) for text in texts]

    for parsed_text in parsed_texts:
        if len(parsed_text.sample) not in parsed_text.end_of_sentences:
            parsed_text.end_of_sentences.append(len(parsed_text.sample))

    quotes = []
    tags = []

    for match in matches:
        # Don't bother making quotes out of party matches
        if match.type == 'party':
            continue

        sub = match.match.range
        spans = texts_tokens[match.match.source].spans

        wmatch_start = spans[max(sub[0], 0)][0]
        wmatch_end = spans[min(sub[1]-1, len(spans)-1)][1]

        tags.append(MatchTag(start=wmatch_start,
                             end=wmatch_end,
                             type=match.type,
                             id=match.id,
                             source=match.match.source))

        for i, eos in enumerate(parsed_texts[match.match.source].end_of_sentences):
            if eos >= wmatch_start:
                if i != 0:
                    match_start = parsed_texts[match.match.source].end_of_sentences[i-1] + 1
                    match_end = eos
                else:
                    match_start = 0
                    match_end = parsed_texts[match.match.source].end_of_sentences[0] + 1
                break
        else:
            print "Fallthrough"
            match_start = 0
            match_end = len(texts[match.match.source])

        match_start = max(spans[max(sub[0] - 10, 0)][0], match_start)
        match_end = min(spans[min(sub[1] + 10, len(spans)-1)][1], match_end)

        quote_doc = {'constituency_ids': [],
                     'party_ids': [],
                     'candidate_ids': [],
                     'quote_span': (match_start, match_end),
                     'match_text': match.match.source}

        if match.type == 'candidate' or match.type == 'candidate_extra':
            quote_doc['candidate_ids'].append((match.id, wmatch_start, wmatch_end))
        #elif match_type == 'party':
        #    quote_doc['party_ids'].append((match_id, wmatch_start, wmatch_end))
        elif match.type == 'constituency':
            quote_doc['constituency_ids'].append((match.id, wmatch_start, wmatch_end))

        quotes.append(quote_doc)

        #print quote_doc

    similar_pairs = []
    for i, quote1 in enumerate(quotes):
        for j, quote2 in enumerate(quotes):
            if quote1['match_text'] == quote2['match_text'] and range_overlap(quote1['quote_span'], quote2['quote_span']):
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

    # Split up excessively long groups of quotes.
    split_groups = []
    for group in groups:
        quote_ids = sorted(list(group))

        for i in range(0,len(quote_ids),10):
            split_groups.append(quote_ids[i:i + 10])

    print split_groups

    merged_quotes = []
    for group in split_groups:
        quote = {'constituency_ids': list(set(sum([quotes[i]['constituency_ids'] for i in group], []))),
                 ##'party_ids': list(set(sum([quotes[i]['party_ids'] for i in group], []))),
                 'candidate_ids': list(set(sum([quotes[i]['candidate_ids'] for i in group], []))),
                 'quote_span': (min(quotes[i]['quote_span'][0] for i in group),
                                max(quotes[i]['quote_span'][1] for i in group),),
                 'match_text': quotes[i]['match_text'],}
 
        merged_quotes.append(quote)
    
    quotes = merged_quotes 

    print "  Total {} quotes".format(len(quotes))
   
    return MatchQuotes(quotes=quotes,
                       tags=tags) 

def resolve_candidates(doc_user, doc_possible, doc_machine):
    resolved_candidates = []

    poss_ids = {candidate['id'] for candidate in doc_possible['candidates']}

    # Add candidates that users have added that the machine didn't find.
    for candidate_id in doc_user['candidates']['confirm']:
        if candidate_id not in poss_ids:
            candidate = get_candidate(candidate_id)

            if 'deleted' not in candidate or not candidate['deleted']:
                candidate['state'] = 'confirmed'
                resolved_candidates.append(candidate)

    # Add candidates that the machine found.
    for candidate in doc_possible['candidates']:
        candidate_state = 'unknown'

        if doc_machine:
            if candidate['id'] in doc_machine['candidates']['confirm']:
                candidate_state = 'confirmed_ml'
            elif candidate['id'] in doc_machine['candidates']['remove']:
                candidate_state = 'removed_ml'

        if doc_user:
            if candidate['id'] in doc_user['candidates']['confirm']:
                candidate_state = 'confirmed'
            elif candidate['id'] in doc_user['candidates']['remove']:
                candidate_state = 'removed'

        candidate_ = get_candidate(candidate['id'])
        if 'deleted' not in candidate_ or not candidate_['deleted']:
            candidate_['state'] = candidate_state
            resolved_candidates.append(candidate_)

    return resolved_candidates

def resolve_constituencies(doc_user, doc_possible):
    resolved_constituencies = []
 
    # Add constituencies that users have added that the machine didn't find.
    for constituency_id in doc_user['constituencies']['confirm']:
        if not any([constituency_id == constituency['id'] for constituency in doc_possible['constituencies']]):
            constituency = constituencies_index[constituency_id]
            constituency['state'] = 'confirmed'
            constituency['score'] = 1.5
            resolved_constituencies.append(constituency)

    # Add constituencies that the machine found.
    for constituency in doc_possible['constituencies']:
        constituency_state = 'unknown'

        if constituency['id'] in doc_user['constituencies']['confirm']:
            constituency_state = 'confirmed'
        elif constituency['id'] in doc_user['constituencies']['remove']:
            constituency_state = 'removed'

        constituency_ = constituencies_index[constituency['id']]
        constituency_['id'] = constituency_['id']
        constituency_['state'] = constituency_state
        constituency_['score'] = 1.0

        resolved_constituencies.append(constituency_)

    return resolved_constituencies


def resolve_quotes(doc, verbose=False):
    texts = [doc['page']['text'],
             doc['page']['title']]

    candidates = {candidate['id']: candidate for candidate in doc['candidates'] if candidate['state'] not in ['removed', 'removed_ml']}
    constituencies = {constituency['id']: constituency for constituency in doc['constituencies'] if constituency['state'] != 'removed'}

    for quote_doc in doc['quotes']:
        # Grab info, only include if they're in the final resolved constituencies/candidates 
        quote_doc['candidates'] = [candidates[candidate_id[0]] for candidate_id in quote_doc['candidate_ids'] if candidate_id[0] in candidates]
        quote_doc['constituencies'] = [constituencies[constituency_id[0]] for constituency_id in quote_doc['constituency_ids'] if constituency_id[0] in constituencies]

        # Don't bother pulling out quotes mentioning parties
        #quote['parties'] = [parties[party_id[0]] for party_id in quote['party_ids']]

        quote_text = texts[quote_doc['match_text']][quote_doc['quote_span'][0]:quote_doc['quote_span'][1]]
    
        quote_doc['text'] = quote_text

        #print "QLEN", float(len(quote_text)) / len(texts[0])

        offset = quote_doc['quote_span'][0]
       
        tags = [((s-offset, e-offset), "<a href='/person/{0}' class='quote-candidate-highlight quote-candidate-{0}-highlight'>".format(id), "</a>") for id, s, e in quote_doc['candidate_ids'] if id in candidates]
        tags += [((s-offset, e-offset), "<a href='/constituency/{0}' class='quote-constituency-highlight quote-constituency-{0}-highlight'>".format(id), "</a>") for id, s, e in quote_doc['constituency_ids'] if id in constituencies]
 
        quote_html = add_tags(quote_text, tags)
        quote_doc['tags'] = tags
        quote_doc['html'] = quote_html.strip()

    tags = []

    doc['tags'] = [MatchTag(*tag) for tag in doc['tags']]

    for tag in doc['tags']:
        if tag.source == 0:
            if tag.type == "constituency" and tag.id in constituencies:
                tags.append(((tag[0], tag[1]), "<a href='/constituency/{0}' class='quote-constituency-highlight quote-constituency-{0}-highlight'>".format(tag[3]), "</a>"))
            elif tag.type in ["candidate", "candidate_extra"] and tag.id in candidates:
                tags.append(((tag[0], tag[1]), "<a href='/person/{0}' class='quote-candidate-highlight quote-candidate-{0}-highlight'>".format(tag[3]), "</a>"))

    clash = False
    for tag1, tag2 in combinations(doc['tags'], 2):
        if tag1.source == tag2.source and tag1.id != tag2.id and (tag1[0], tag1[1]) == (tag2[0], tag2[1]):
            if tag1.type == "constituency" and tag1.id in constituencies:
                tag1_ok = True
            elif tag1.type in ["candidate", "candidate_extra"] and tag1.id in candidates:
                tag1_ok = True
            else:
                tag1_ok = False
            
            if tag2.type == "constituency" and tag2.id in constituencies:
                tag2_ok = True
            elif tag2.type in ["candidate", "candidate_extra"] and tag2.id in candidates:
                tag2_ok = True
            else:
                tag2_ok = False

            if tag1_ok and tag2_ok and not (tag1.type == 'candidate_extra' and tag2.type == 'candidate_extra'):
                clash = True

                if verbose:
                    print "Clash", tag1, tag2

    doc['tagged_html'] = add_tags(doc['page']['text'], tags)
    doc['tag_clash'] = clash
        

def resolve_matches(doc, verbose=False):
    """
        Generate the final description of the tags by combining the machine matched
        tags and the user contributed tags.
    """
    
    if 'user' not in doc:
        doc['user'] = {}

    if 'candidates' not in doc['user']:
        doc['user']['candidates'] = {'confirm': [], 'remove': []}

    if 'constituencies' not in doc['user']:
        doc['user']['constituencies'] = {'confirm': [], 'remove': []}

    if 'possible' in doc:
        doc['candidates'] = resolve_candidates(doc['user'], doc['possible'], doc.get('machine'))
        doc['constituencies'] = resolve_constituencies(doc['user'], doc['possible']) 

    if 'quotes' in doc:
        resolve_quotes(doc, verbose)

    return

if __name__ == "__main__":
    from db import db_articles
    import argparse

    parser = argparse.ArgumentParser(description='Perform matching engine against set of documents')

    parser.add_argument('-d', '--doc', action="store", help="Just this document (MongoDB ObjectID).", default=None) 
    parser.add_argument('-p', '--person', action="store", help="All documents with this person (ID).", default=None) 
    parser.add_argument('-c', '--constituency', action="store", help="All documents with this constituency (ID).", default=None)
    parser.add_argument('-v', '--verbose', action="store_const", help="Be more verbose, explain the matching process.", default=False, const=True)

    a = parser.parse_args(sys.argv[1:])

    db = db_articles

    if a.doc is not None:
        docs = db.find({'_id': ObjectId(a.doc)})
    elif a.person is not None:
        pass
    elif a.constituency is not None:
        docs = db.find({'constituencies.id': a.constituency})
    else:
        docs = db.find() \
                 .sort([('time_added', -1)])

    for doc in docs:
        print >>sys.stderr, doc['keys'], doc['_id']
        print >>sys.stdout, doc['keys'], doc['_id']

        if doc['page'] is not None and doc['page']['text'] is not None:
            doc['matches'], doc['possible'] = add_matches([doc['page']['text'], doc['page']['title']], a.verbose)

            doc['quotes'], doc['tags'] = add_quotes(doc['matches'], [doc['page']['text'], doc['page']['title']])
            
            doc['machine'] = get_machine(doc)

        resolve_matches(doc, a.verbose)

        db.save(doc)

