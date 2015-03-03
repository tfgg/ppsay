# -*- coding: utf-8 -*-
import sys
from text import get_tokens
from ppsay.data import constituencies, constituencies_names, parties, get_candidates

index = {}

def munge_names(names, incumbent, prefix):
    for name in list(names):
        name_tokens = name.split()

        # If we have more than forename-surname, try middlename + surname
        # Catches, e.g. Máirtín Ó Muilleoir
        if len(name_tokens) > 2:
            s = " ".join(name_tokens[1:])

            # Screw you Al Murray
            if s != "Pub Landlord":
                names.append(s)

            s = name_tokens[0] + " " + name_tokens[-1]

            if s != "The Landlord":
                names.append(s)

        # Macdonald -> Mcdonald
        if ' Mac' in name:
            names.append(name.replace('Mac', 'Mc'))
        
        if incumbent:    
            names.append(u"MP {}".format(name))
            names.append(u"{} MP".format(name))

        if prefix is not None:
            names.append(u"{} {}".format(prefix, name))

def ngrams(tokens, n):
    n = min(len(tokens), n)
    for i in range(len(tokens) + 1 - n):
        yield tuple(tokens[i:i+n])

#print list(ngrams([1,2,3,4], 2))
#print list(ngrams([1,2,3,4], 3))
#print list(ngrams([1,2,3,4], 4))
#print list(ngrams([1,2,3,4], 5))

for constituency in constituencies:
    names = set([constituency['name']] + constituencies_names[constituency['id']])

    for name in names:
        tokens, spans = get_tokens(name.lower())

        for ngram in ngrams(tokens, 3):
            if ngram in index:
                index[ngram].append(('constituency', constituency['id']))
            else:
                index[ngram] = [('constituency', constituency['id'])]

for party_id, party in parties.items():
    names = set([party['name']] + parties[party_id]['other_names'])

    for name in names:
        tokens, spans = get_tokens(name.lower())

        for ngram in ngrams(tokens, 3):
            if ngram in index:
                index[ngram].append(('party', party['id']))
            else:
                index[ngram] = [('party', party['id'])]

for candidate in get_candidates():
    names = [candidate['name']] + candidate['other_names']
    munge_names(names, candidate.get("incumbent", False), candidate.get("name_prefix", ''))
    names = set(names)

    for name in names:
        tokens, spans = get_tokens(name.lower())

        for ngram in ngrams(tokens, 3):
            if ngram in index:
                index[ngram].append(('candidate', candidate['id']))
            else:
                index[ngram] = [('candidate', candidate['id'])]


