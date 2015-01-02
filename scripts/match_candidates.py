# -*- coding: utf-8 -*-
import sys

from bson import ObjectId
from pymongo import MongoClient

from ppsay.matches import add_matches

if __name__ == "__main__":
    client = MongoClient()
    db = client.news.articles

    if len(sys.argv) == 1:
        docs = db.find()
    else:
        doc_id = ObjectId(sys.argv[1])
        docs = db.find({'_id': doc_id})
      
    for doc in docs:
      if doc['page'] is None:
        continue
      
      print doc['key']

      add_matches(doc)     
 
      db.save(doc)

