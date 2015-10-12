# -*- coding: utf-8 -*-

import sys
import json
from itertools import combinations, chain

from bson import ObjectId
from ppsay.data import (
    get_constituency,
    get_candidate,
    parties,
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

from match_lookup import (
    get_ngrams,
    index,
)

from namemunge.en import (
    primary_generate_names,
    secondary_generate_names,
)

MatchEntity = namedtuple('MatchEntity', ['type', 'id', 'match']) 
MatchQuotes = namedtuple('MatchQuotes', ['quotes', 'tags'])
Matches = namedtuple('Matches', ['matches', 'possible'])

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

def prescreen_text(texts_tokens, index):
    # Pre-screen with an n-gram match
    ngrams = chain(*[get_ngrams(text_tokens.tokens, n) for n in range(1,4) for text_tokens in texts_tokens])

    poss_matches = set()
    for ngram in ngrams:
        if ngram in index:
            poss_matches |= set(index[ngram])

    return poss_matches

def matches(texts, obj_types, index, verbose=False): 
    texts_tokens = [get_tokens(text.lower()) for text in texts]

    poss_matches = prescreen_text(texts_tokens, index)

    match_entities = []

    # Take candidate matches and refine match
    for obj_type, obj_index in poss_matches:
        ot = obj_types[obj_type]
        object = ot.get_object(obj_index)
        names = [object['name']] + object.get('other_names', [])

        if ot.primary_generate_names:
            primary_names = set(chain(names, ot.primary_generate_names(names, object)))
        else:
            primary_names = names

        if ot.secondary_generate_names:
            secondary_names = set(secondary_generate_names(names, object))
        else:
            secondary_names = None

        have_matches = False
        for match in find_matches(primary_names, *texts_tokens):
            match_entities.append(MatchEntity(type=obj_type, id=obj_index, match=match))
            have_matches = True

        # If we have some definite matches, do some looser matches, e.g. Tim Green -> Mr Green
        if have_matches and secondary_names:
            for match in find_matches(secondary_names, *texts_tokens):
                match_entities.append(MatchEntity(type=obj_type + "_extra", id=obj_index, match=match))
            
    object_ids = {
        obj_type: {x.id for x in match_entities if x.type==obj_type}
        for obj_type in obj_types
    }

    if verbose:
        for obj_type, ids in object_ids.items():
            print "  Found {} of {}".format(len(ids), obj_type)
    
    # Load in squish phrases for matched objects, e.g. Gordon Ramsay for Gordon.
    num_squish = 0
    for obj_type in object_ids:
        ot = obj_types[obj_type]

        for obj_id in object_ids[obj_type]:
            phrases = ot.squish_index.get(obj_id)
    
            if phrases:
                for match in find_matches(phrases, *texts_tokens):
                    match_entities.append(MatchEntity(type='squish', id=None, match=match))
                    num_squish += 1

    # Fixes complaint about https://www.electionmentions.com/article/553ab95f238f31772f962b5d
    extra_squishes = ['Ian Smart']
    for match in find_matches(extra_squishes, *texts_tokens):
        match_entities.append(MatchEntity(type='squish', id=None, match=match))
        num_squish += 1

    if verbose:
        print "  Found {} squishes".format(num_squish)
        print "  Total {} matches".format(len(match_entities))

    if verbose:
        for match_entity in match_entities:
            print "   ", match_entity

    return match_entities

def trim_matches(match_entities, object_ids, verbose=False):
    match_entities = list(resolve_overlaps(match_entities, verbose))

    if verbose:
        print "  Total {} matches remaining".format(len(match_entities))
    
    # Remove extra matches which no longer have a parent match
    def filter_extra(match_entity):
        if match_entity.type.endswith('_extra'):
            parent_type = match_entity.type[:-len('_extra')]
            if match_entity.id not in object_ids[parent_type]:
                if verbose: 
                    print match_entity, "not got parent"
                return False
        return True

    match_entities = filter(filter_extra, match_entities)

    return match_entities

ObjectType = namedtuple(
    'ObjectType',
    [
        'get_object',
        'squish_index',
        'primary_generate_names',
        'secondary_generate_names'
    ],
)

obj_types = {
    'candidate': ObjectType(
        get_object=get_candidate,
        squish_index={},
        primary_generate_names=primary_generate_names,
        secondary_generate_names=secondary_generate_names,
    ),
    'constituency': ObjectType(
        get_object=get_constituency,
        squish_index=squish_constituencies,
        primary_generate_names=None, 
        secondary_generate_names=None,
    ),
    'party': ObjectType(
        get_object=lambda obj_id: parties[obj_id],
        squish_index={},
        primary_generate_names=None, 
        secondary_generate_names=None,
    ),
}

def add_matches(texts, verbose=False):  
    match_entities = matches(texts, obj_types, index, verbose=verbose)
    
    object_ids = {
        obj_type: {x.id for x in match_entities if x.type==obj_type}
        for obj_type in obj_types
    }

    match_entities = trim_matches(match_entities, object_ids, verbose=verbose)

    def unique_obj(objs, obj_type):
        return {x.id for x in objs if x.type == obj_type}

    possible = {
        'parties': [{'id': x} for x in unique_obj(match_entities, 'party')],
        'constituencies': [{'id': x} for x in unique_obj(match_entities, 'constituency')],
        'candidates': [{'id': x} for x in unique_obj(match_entities, 'candidate')],
    }

    return Matches(matches=match_entities,
                   possible=possible)


MatchTag = namedtuple(
    'MatchTag',
    [
        'start',
        'end',
        'type',
        'id',
        'source',
    ]
)

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
                    match_end = parsed_texts[match.match.source].end_of_sentences[0]
                break
        else:
            print "Fallthrough"
            match_start = 0
            match_end = len(texts[match.match.source])

        max_quote_len = 40
        match_start = max(spans[max(sub[0] - max_quote_len/2, 0)][0], match_start)
        match_end = min(spans[min(sub[1] + max_quote_len/2, len(spans)-1)][1], match_end)

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
        j = i + 1

        if j >= len(quotes): continue

        quote2 = quotes[j]

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

    merged_quotes = []
    for group in split_groups:
        quote = {'constituency_ids': list(set(sum([quotes[i]['constituency_ids'] for i in group], []))),
                 ##'party_ids': list(set(sum([quotes[i]['party_ids'] for i in group], []))),
                 'candidate_ids': list(set(sum([quotes[i]['candidate_ids'] for i in group], []))),
                 'quote_span': (min(quotes[i]['quote_span'][0] for i in group),
                                max(quotes[i]['quote_span'][1] for i in group),),
                 'match_text': quotes[i]['match_text'],}
        
        eos_left = quote['quote_span'][0] == 0 or (quote['quote_span'][0] - 1) in parsed_texts[quote['match_text']].end_of_sentences
        eos_right = quote['quote_span'][1] in parsed_texts[quote['match_text']].end_of_sentences

        quote['truncated'] = {'left': not eos_left,
                              'right': not eos_right,}
 
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
            constituency = get_constituency(constituency_id)
            constituency['state'] = 'confirmed'
            resolved_constituencies.append(constituency)

    # Add constituencies that the machine found.
    for constituency in doc_possible['constituencies']:
        constituency_state = 'unknown'

        if constituency['id'] in doc_user['constituencies']['confirm']:
            constituency_state = 'confirmed'
        elif constituency['id'] in doc_user['constituencies']['remove']:
            constituency_state = 'removed'

        constituency_ = get_constituency(constituency['id'])
        constituency_['id'] = constituency_['id']
        constituency_['state'] = constituency_state

        resolved_constituencies.append(constituency_)

    return resolved_constituencies


def resolve_quotes(texts, doc, verbose=False):
    #texts = [doc['page']['text'],
    #         doc['page']['title']]

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

    doc['tagged_html'] = add_tags(texts[0], tags)
    doc['tag_clash'] = clash
        

def resolve_matches(texts, doc, verbose=False):
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
        resolve_quotes(texts, doc, verbose)

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

