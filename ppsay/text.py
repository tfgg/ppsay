# -*- coding: utf-8 -*-

import re

def is_sublist(a, b):
    i = 0
    
    if a == []: return

    while i != len(b):

        if b[i:i + len(a)] == a:
            yield (i, i + len(a))

        i = i + 1

sep_re = re.compile(u'[ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+')
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
