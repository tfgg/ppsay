import re
import sys
import codecs

tag = re.compile('<([a-z]|\/[a-z])>')

text = codecs.open(sys.argv[1], 'r', 'utf-8').read()

tags = {
    'q': 'startquote',
    '/q': 'endquote',
    's': 'startsent',
    '/s': 'endsent',
}

indexes = {
    tag: []
    for _,tag in tags.items()
}

curr = 0
s = ""

for fragment in tag.split(text):
    if fragment in tags:
        indexes[tags[fragment]].append(curr)
    else:
        curr += len(fragment)
        s += fragment

print indexes
print s
for i in range(len(s)+1):
    vec = [0] * len(indexes)
    for j, tag in enumerate(indexes):
        if i in indexes[tag]:
            vec[j] = 1

    if i < len(s):
        print repr(s[i]), vec
    else:
        print "EF", vec

print [tag for tag in indexes]

