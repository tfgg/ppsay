from ppsay.text import normalize, get_tokens
from ppsay.ss import Text
import sys

text = normalize(open(sys.argv[1]).read().decode('utf-8'))

t = Text(text)

sentences = []

last = 0

for eos in t.end_of_sentences:
    sentences.append(text[last:eos].strip())
    last = eos

titles = {'mr', 'mrs', 'dr', 'doctor', 'prof', 'professor', 'sir', 'mp', 'mbe', 'miss', 'master', 'ms', 'lord'}

first_names = {name.strip().lower() for name in open('data/first_names.txt')}
surnames = {name.strip().lower() for name in open('data/surnames.txt')}


def is_capitalized(token):
    if ord('A') <= ord(token[0]) <= ord('Z'):
        return True
    else:
        return False

for sentence in sentences:
    tokens = get_tokens(sentence)

    tagging = ['W']

    for token in tokens[0]:
        iscap = is_capitalized(token)
        fn = token.lower() in first_names
        sn = token.lower() in surnames
        tit = token.lower() in titles

        lastcat = tagging[-1]

        cat = 'W'
        if iscap and fn:
            cat = 'NAME'
        if iscap and sn:
            cat = 'NAME'
        if tit:
            cat = 'TITLE'
        if lastcat == 'NAME' and iscap:
            cat = 'NAME'

        tagging.append(cat)
        
        #print u"{}\t{}".format(cat, token).encode('utf-8')
        print u"{}".format(token).encode('utf-8')

    print "EOS"

