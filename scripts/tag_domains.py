# -*- coding: utf-8 -*-
import json
from pymongo import MongoClient
from ppsay.domains import add_domain

client = MongoClient()

db = client.news.articles

docs = db.find()

for doc in docs:
    add_domain(doc)
    db.save(doc)

