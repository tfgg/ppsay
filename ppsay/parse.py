# -*- coding: utf-8 -*-
import sys
import re
import json

from bson import ObjectId
from pymongo import MongoClient

client = MongoClient()

db = client.news.articles

from collections import Counter

titles = {'MP', 'MEP', 'Mr', 'Mrs', 'Miss', 'Ms', 'Dr'}

constituencies = json.load(open('parse_data/constituencies.json'))

word_regex = re.compile(r'(\w+)')

def find_word_boundaries(s):
  word_matches = word_regex.finditer(s)

  words = [word_match.span() for word_match in word_matches]

  return words


s = db.find_one({'_id': ObjectId(sys.argv[1])})['page']['text']

def is_capitalized(s):
  return s[0] == s[0].upper()

def extract_tokens(s, ws):
  for a, b in ws:
    yield s[a:b]

def extract_caps(s, ws):
  caps = []
  curr_caps = []

  for word in extract_tokens(s, ws):
    if word[0] == word[0].upper():
      curr_caps.append(word)
    elif len(curr_caps) != 0:
      caps.append(curr_caps)
      curr_caps = []

  return caps

ws = find_word_boundaries(s)

word_counter = Counter(" ".join(w) for w in extract_caps(s, ws))

print word_counter

#for word in word_counter:
#  for constituency in constituencies:
#    if word in constituency:
#      print word, constituency

