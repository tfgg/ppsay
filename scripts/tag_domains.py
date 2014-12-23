# -*- coding: utf-8 -*-
import json
from pymongo import MongoClient
from urlparse import urlparse

client = MongoClient()

db = client.news.articles

docs = db.find()

for doc in docs:
  parsed_url = urlparse(doc['key'])
  print parsed_url.netloc
  doc['domain'] =  parsed_url.netloc
  db.save(doc)

