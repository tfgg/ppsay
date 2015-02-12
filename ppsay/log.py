import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flask import request

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_log = db_client.news.action_log

def log(action, url, extra_data):
    doc = {'time_now': datetime.now(),
           'client_ip': request.remote_addr,
           'action': action,
           'url': url,
           'extra': extra_data}

    doc_id = db_log.save(doc)

    return doc_id

