import sys
import math
from collections import Counter

titles = {'mr', 'mrs', 'professor', 'dr', 'prof', 'sir', 'mbe', 'miss', 'master', 'ms', 'lord','dame','duke','duchess'}
roles = {'doctor', 'professor', 'president', 'prime', 'minister', 'secretary', 'chancellor', 'treasury', 'coroner', 'editor', 'parliamentary', 'candidate', 'activist', 'spokesman', 'ambassador', 'mp','mps','leader','minister','whip','shadow','chief','defence','international','development','cabinet','political','correspondent','judge','di','inspector','adviser','director','general','executive','councillor', 'hopeful','pm','mayor','deputy','mayors','senior','adviser','advisors','queen','speaker','coroner','fm','chairman','clerk','ministers','assistant','employment','business','justice','mandarin','health','backbencher'}
months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',}
parties = {'labour', 'conservative', 'green', 'liberal', 'democrat', 'libdem', 'tory', 'bnp', 'ukip', 'plaid', 'cymru', 'tories', 'kippers', 'party','conservatives','snp','con','lab','lib'}

top100 = {word.strip().lower() for word in open('top100.txt')}
first_names = {name.strip().lower() for name in open('first_names.txt')}
surnames = {name.strip().lower() for name in open('surnames.txt')}
countries = {word.strip().lower() for name in open('countries.txt') for word in name.decode('utf-8').strip().split() if word.strip().lower() not in top100}
surrounding = {word.strip().lower() for word in open('surround.txt')} - top100 - roles - titles

def is_capitalized(token):
    if ord('A') <= ord(token[0]) <= ord('Z'):
        return True
    else:
        return False

X = []
Y = []

cats = ['EOS', 'W', 'TITLE', 'NAME', 'ROLE', 'PARTY', 'COUN']
print cats

def get_token_vec(token):
    iscap = 1 if is_capitalized(token) else 0
    fn = 1 if token.lower() in first_names else 0
    sn = 1 if token.lower() in surnames else 0
    tit = 1 if token.lower() in titles else 0
    ro = 1 if token.lower() in roles else 0
    mon = 1 if token.lower() in months else 0
    par = 1 if token.lower() in parties else 0
    t100 = 1 if token.lower() in top100 else 0
    cu = 1 if token.lower() in countries else 0
    sur = 1 if token.lower() in surrounding else 0
    pos = 1 if token == 's' else 0

    return (iscap, fn, sn, tit, ro, mon, par, t100, cu, sur, pos)


def get_cat_vec(lastcat):
    return (
        1 if lastcat==0 else 0,
        1 if lastcat==1 else 0,
        1 if lastcat==2 else 0,
        1 if lastcat==3 else 0,
        1 if lastcat==4 else 0,
        1 if lastcat==5 else 0,
        1 if lastcat==6 else 0,
    )


def parse_input(f):
    lines = list(f)

    tokens = []
    real_cats = []

    for i, line in enumerate(lines):
        cols = line.split()

        if len(cols) > 1:
            token = cols[1]
            real_cat = cats.index(cols[0])
        else:
            token = cols[0]

            if token == 'EOS':
                token = None
                real_cat = 0
            else:
                real_cat = None

        tokens.append(token)
        real_cats.append(real_cat)

    return tokens, real_cats

surrounding = Counter()

for path in sys.argv[3:]:
    f = open(path)

    tokens, real_cats = parse_input(f)

    # Start at EOS
    lastcat = 0
    num_name = Counter()

    for i, (token, real_cat) in enumerate(zip(tokens, real_cats)):
        if token:
            if i - 1 >= 0 and tokens[i-1]:
                last_token_vec = get_token_vec(tokens[i-1])

                if real_cat == 3:
                    surrounding[tokens[i-1]] += 1
            else:
                last_token_vec = get_token_vec(" ")

            token_vec = get_token_vec(token)

            if i + 1 < len(tokens) and tokens[i+1]:
                next_token_vec = get_token_vec(tokens[i+1])
                
                if real_cat == 3:
                    surrounding[tokens[i+1]] += 1
            else:
                next_token_vec = get_token_vec(" ")

            state_vec = (
                math.log10(num_name[token] + 0.1),
            #    float(i) / num_lines,
            )

            x = last_token_vec + token_vec + next_token_vec + state_vec + get_cat_vec(lastcat) 
            y = (real_cat,)

            X.append(x)
            Y.append(y)


            if real_cat == 3:
                num_name[token] += 1

        lastcat = real_cat

from sklearn.linear_model import LogisticRegression
import numpy as np

X = np.reshape(X,(len(X), len(X[0])))
Y = np.reshape(Y,(len(Y),))

C = float(sys.argv[1])

model = LogisticRegression(class_weight='balanced',multi_class='ovr',solver='lbfgs',C=C)
model.fit(X,Y)

print model.classes_

confusion = np.zeros((len(cats), len(cats)))

for path in sys.argv[2:3]:
    f = open(path)

    tokens, real_cats = parse_input(f)

    # Start at EOS
    lastcat = 0
    num_name = Counter()

    for i, (token, real_cat) in enumerate(zip(tokens, real_cats)):
        if token:
            if i - 1 >= 0 and tokens[i-1]:
                last_token_vec = get_token_vec(tokens[i-1])
            else:
                last_token_vec = get_token_vec(" ")

            token_vec = get_token_vec(token)

            if i + 1 < len(tokens) and tokens[i+1]:
                next_token_vec = get_token_vec(tokens[i+1])
            else:
                next_token_vec = get_token_vec(" ")

            state_vec = (
                math.log10(num_name[token] + 0.1),
            #    float(i) / num_lines,
            )

            x = last_token_vec + token_vec + next_token_vec + state_vec + get_cat_vec(lastcat) 

            predicted_cat = model.predict(x)

            lastcat = predicted_cat

            if real_cat:
                print cats[real_cat], cats[predicted_cat[0]], token
                confusion[real_cat, predicted_cat[0]] += 1
            else:
                print cats[predicted_cat[0]], token
 
            if predicted_cat == 3:
                num_name[token] += 1
        else:
            lastcat = 0
            print 'EOS'
        

print "\t{}".format("\t".join(cats))

for i in range(len(cats)):
    print "{}\t".format(cats[i]),
    for j in range(len(cats)):
        print "{}\t".format(confusion[i, j]),
    print

name_recall = confusion[3,3] / np.sum(confusion[3,:])
name_precision = confusion[3,3] / np.sum(confusion[:,3])

print name_recall, name_precision
