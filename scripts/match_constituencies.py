# -*- coding: utf-8 -*-
import sys
import json
import re
from collections import Counter

from bson import ObjectId
from pymongo import MongoClient

sep_re = re.compile(u'[ ,‘’“”.!;:\'"?\-=+_\r\n\t()]+')

cardinal_directions = ['north east', 'south east', 'south west', 'north west', 'north', 'south', 'east', 'west']

def is_sublist(a, b):
    i = 0
    
    if a == []: return True

    while True:
        if i == len(b): return False

        if b[i:i + len(a)] == a:
            return True
        else:
            i = i + 1

def find_matches(names, text_tokens, title_tokens):
    names = [[y.lower() for y in sep_re.split(x)] for x in names]

    for name in names:
        ii = is_sublist(name, title_tokens)

        if ii:
            return 1.0, 'title', name, ii

    for name in names:
        ii = is_sublist(name, text_tokens)

        if ii:
            return 1.0, 'text', name, ii

    return None

if __name__ == "__main__": 
    client = MongoClient()
    db = client.news.articles

    if len(sys.argv) == 1:
        docs = db.find()
    else:
        doc_id = ObjectId(sys.argv[1])
        docs = db.find({'_id': doc_id})

    constituencies = json.load(open('parse_data/constituencies.json'))
    constituency_names = json.load(open('parse_data/constituencies_other_names.json'))

    for doc in docs:
      if doc['page'] is None:
        continue
      
      print doc['key']

      text = doc['page']['text'].lower()
      title = doc['page']['title'].lower()
      title_tokens = sep_re.split(title)
      text_tokens = sep_re.split(text)

      possible_constituency_matches = {}

      for constituency in constituencies:
        names = constituency_names[constituency['id'].split(':')[-1]]

        score = find_matches(names, text_tokens, title_tokens)

        if score is None:
            continue
        else:
          print constituency['name'], score[0], score[2]

          constituency['score'] = score[0]
          constituency['id_snip'] = constituency['id'].split(':')[1]
          possible_constituency_matches[constituency['id_snip']] = constituency

      doc['possible_constituency_matches'] = possible_constituency_matches.values()

      db.save(doc)

