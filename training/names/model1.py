import sys

titles = {'mr', 'mrs', 'dr', 'doctor', 'prof', 'professor', 'sir', 'mp', 'mbe', 'miss', 'master', 'ms', 'lord'}

first_names = {name.strip().lower() for name in open('first_names.txt')}
surnames = {name.strip().lower() for name in open('surnames.txt')}

def is_capitalized(token):
    if ord('A') <= ord(token[0]) <= ord('Z'):
        return True
    else:
        return False

f = open(sys.argv[1])

lastcat = 'EOS'
for line in f:
    cols = line.split()
    real_cat = cols[0]

    if len(cols) > 1:
        token = cols[1]
    else:
        token = None

    if token:
        iscap = is_capitalized(token)
        fn = token.lower() in first_names
        sn = token.lower() in surnames
        tit = token.lower() in titles

        cat = 'W'
        if iscap and fn:
            cat = 'NAME'
        if iscap and sn:
            cat = 'NAME'
        if tit:
            cat = 'TITLE'
        if lastcat == 'NAME' and iscap:
            cat = 'NAME'

        print u"{}\t{}\t{}".format(cat, real_cat, token).encode('utf-8')
    else:
        print "EOS"

    lastcat = cat

