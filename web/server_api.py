# -*- coding: utf-8 -*-
import requests
import json
import math
import iso8601
import pytz

from datetime import timedelta, datetime

from bson import ObjectId

from flask import (
    Blueprint,
    url_for,
    render_template,
    request,
    jsonify,
    abort,
    redirect,
    make_response
)

from ppsay.stream import StreamItem

app = Blueprint('api',
                __name__,
                template_folder='templates')

def process_stream_item(si):
    if si.data['date_published'] is not None:
        date_published = si.data['date_published'].isoformat()
    else:
        date_published = None

    return {
        'stream_item_id': str(si.id),
        'title': si.data['title'],
        'quote': si.data['quote'],
        'url': si.data['url'],
        'date_order': si.date_order.isoformat(),
        'date_published': date_published,
        'people_ids': si.streams['people'],
        'post_ids': si.streams['constituencies'],
        'article_id': str(si.data['article_id']),
    }

@app.route('/api/stream')
def get_stream():
    datetime_since = iso8601.parse_date(request.args.get('since'))

    stream = StreamItem.get_since(datetime_since)

    return jsonify({
        'datetime_since': str(datetime_since),
        'num_stream_items': len(stream),
        'stream_items': [process_stream_item(stream_item) for stream_item in stream],
    })
 
