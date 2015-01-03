from datetime import datetime
from pymongo import MongoClient
from flask import request

db_client = MongoClient()
db_log = db_client.news.action_log

def log(action, url, extra_data):
    doc = {'time_now': datetime.now(),
           'client_ip': request.remote_addr,
           'action': action,
           'url': url,
           'extra': extra_data}

    doc_id = db_log.save(doc)

    return doc_id

