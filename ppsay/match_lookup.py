# -*- coding: utf-8 -*-
import sys
from collections import defaultdict
from itertools import chain

from text import get_tokens
from ppsay.data import get_constituencies, parties, get_candidates
from namemunge.en import primary_generate_names

def get_ngrams(tokens, n):
    n = min(len(tokens), n)
    for i in range(len(tokens) + 1 - n):
        yield tuple(tokens[i:i+n])

index = defaultdict(list)

def update_index(index, names, tag, id):
    for name in names:
        tokens, _ = get_tokens(name.lower())

        for ngram in get_ngrams(tokens, 3):
            index[ngram].append((tag, id))

for constituency in get_constituencies():
    names = set([constituency['name']] + constituency['other_names'])
    update_index(index, names, 'constituency', constituency['id'])

for party_id, party in parties.items():
    names = set([party['name']] + parties[party_id]['other_names'])
    update_index(index, names, 'party', party['id'])

for candidate in get_candidates():
    original_names = [candidate['name']] + candidate['other_names']

    extra_names = primary_generate_names(original_names,
                                         candidate.get("incumbent", False),
                                         candidate.get("name_prefix", ''))

    names = set(chain(original_names, extra_names))
    update_index(index, names, 'candidate', candidate['id'])

