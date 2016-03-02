# -*- coding: utf-8 -*-

import re
from collections import namedtuple

def is_sublist(a, b):
    i = 0
    
    if a == []: return

    while i != len(b):

        if b[i:i + len(a)] == a:
            yield (i, i + len(a))

        i = i + 1

sep_re = re.compile(u'[ ,‘’“”.!;:\'`"?\-=+_\r\n\t()\xa0><@]+')
token_re = re.compile(u'([^ ,‘’“”.!;:\'`"?\-=+_\r\n\t()\xa0><@]+)')

TextTokens = namedtuple("TextTokens", ['tokens', 'spans'])

normalize_pairs = [
    (u"“", u'"'),
    (u"”", u'"'),
    (u"‘", u"'"),
    (u"’", u"'"),
    (u"\xa0", u" "), # Non-breaking space
    (u"\x2013", u"-"), # en-dash
    (u"\x2014", u"-"), # en-dash
]

def normalize(s):
    for a, b in normalize_pairs:
        s = s.replace(a,b)
    return s

def get_tokens(s):
    tokens = []
    spans = []
    
    for match in token_re.finditer(s):
        tokens.append(match.groups()[0])
        spans.append(match.span())
        
    return TextTokens(tokens=tokens, spans=spans)

TextMatch = namedtuple("TextMatch", ['source', 'range', 'text'])

def find_matches(ss, *texts_tokens):
  for s in ss:
    target_tokens = get_tokens(s.lower())

    for i, text_tokens in enumerate(texts_tokens):
        for sub in is_sublist(target_tokens.tokens, text_tokens.tokens):
            yield TextMatch(source=i, range=sub, text=s)

def range_overlap(a, b):
    if a[1] <= b[0] or b[1] <= a[0]:
        return False
    else:
        return True

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

if __name__ == "__main__":
    import sys
    print normalize(open(sys.argv[1]).read().decode('utf-8'))

