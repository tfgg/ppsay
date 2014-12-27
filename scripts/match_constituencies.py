# -*- coding: utf-8 -*-
import json
from pymongo import MongoClient
from collections import Counter

client = MongoClient()

db = client.news.articles

docs = db.find()

cardinal_directions = ['north east', 'south east', 'south west', 'north west', 'north', 'south', 'east', 'west']

def score_match(constituency, text, title):
    names = [constituency]
    name_tokens = constituency.split()

    # Replace " and " with " & "
    for name in list(names):
        if " and " in name:
            names.append(name.replace(" and ", " & "))

    # Transpose directions, e.g. Durham North -> North Durham
    for name in list(names):
        for direction in cardinal_directions:
          if constituency.endswith(direction):
            name_ = direction + " " + constituency[:-len(direction)].strip()
            names.append(name_)
            break

    # Undo commas, e.g. Durham, City of -> City of Durham
    # Also remove commas e.g. Sheffield, Hallam -> Sheffield Hallam
    # And remove first word, e.g. Shieffield, Hallam -> Hallam
    for name in list(names):
        if ',' in constituency:
            tokens = [x.strip() for x in constituency.split(',')]

            names.append(" ".join(tokens))

            if " and " not in constituency:
                names.append(" ".join(tokens[1:]))
                names.append(" ".join(reversed(tokens)))

    # Remove "upon tyne" to fix some Newcastle matching
    for name in list(names):
        name_ = name.replace(' upon tyne', '')
        names.append(name_)
     
    # Filter out Southamton, Test --> Test
    names = [x for x in names if x != 'test']

    for name in names:
        if name in text or name in title:
            return 1.0
    
    return 0.0

if __name__ == "__main__": 
    constituencies = json.load(open('parse_data/constituencies.json'))

    for doc in docs:
      if doc['page'] is None:
        continue
      
      print doc['key']

      text = doc['page']['text'].lower()
      title = doc['page']['title'].lower()

      possible_constituency_matches = {}

      for constituency in constituencies:
        score = score_match(constituency['name'].lower(), text, title)

        if score > 0.0:
          print constituency['name'], score

          constituency['score'] = score
          constituency['id_snip'] = constituency['id'].split(':')[1]
          possible_constituency_matches[constituency['id_snip']] = constituency

      doc['possible_constituency_matches'] = possible_constituency_matches.values()

      db.save(doc)

