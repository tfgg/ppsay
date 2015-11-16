import time
import json
from collections import Counter, defaultdict

from bson import ObjectId

from flask import (
    Blueprint,
    render_template,
    request,
)

from flask.ext.login import login_required

from ppsay.db import (
    db,
    db_articles,
    db_action_log,
    db_domains,
)
from ppsay.page import Page

app = Blueprint('dashboard',
                __name__,
                template_folder='templates')

dashboard_queries = [
    {
        'db': 'pages',
        'type': 'count',
        'template': 'count',
        'query': {},
        'id': 'num_pages',
        'name': 'Number of pages',
    },
    {
        'db': 'articles',
        'type': 'count',
        'query': {},
        'template': 'count',
        'id': 'num_articles',
        'name': 'Number of articles',
    },
    {
        'db': 'pages',
        'type': 'aggregate',
        'template': 'timeseries',
        'query': [
            {
                '$match': {
                    'date_published': {
                        '$ne': None
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'd': {'$dayOfMonth': '$date_published'},
                        'm': {'$month': '$date_published'},
                        'y': {'$year': '$date_published'},
                    },
                    'total': { '$sum': 1 }
                }
            },
        ],
        'id': 'timeseries_pages',
        'name': 'Pages over time',
        'value': lambda d: d['total'],
        'xlabel': 'Time',
        'ylabel': '#Published',
    },
    {
        'db': 'articles',
        'type': 'aggregate',
        'template': 'timeseries',
        'query': [
            {
                '$match': {
                    'time_added': {
                        '$ne': None
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'd': {'$dayOfMonth': '$time_added'},
                        'm': {'$month': '$time_added'},
                        'y': {'$year': '$time_added'},
                    },
                    'total': { '$sum': 1 }
                }
            },
        ],
        'id': 'timeseries_articles',
        'name': 'Articles over time',
        'value': lambda d: d['total'],
        'xlabel': 'Time',
        'ylabel': '#Added',
    },
    {
        'db': 'articles',
        'type': 'aggregate',
        'template': 'timeseries',
        'query': [
            {
                '$match': {
                    'time_added': {
                        '$ne': None
                    },
                    'analysis.machine': {
                        '$ne': None
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'd': {'$dayOfMonth': '$time_added'},
                        'm': {'$month': '$time_added'},
                        'y': {'$year': '$time_added'},
                    },
                    'confirm': { '$sum': { '$size': "$analysis.machine.candidates.confirm" } },
                    'remove': { '$sum': { '$size': "$analysis.machine.candidates.remove" } },
                }
            },
        ],
        'id': 'timeseries_classifier_candidates',
        'name': 'Candidate classifier',
        'value': lambda d: float(d['confirm']) / (d['confirm'] + d['remove']),
        'xlabel': 'Time',
        'ylabel': '#Tags confirmed / #Total tags',
    },
    {
        'db': 'events',
        'type': 'count',
        'template': 'count',
        'query': {'event': 'article_click'},
        'id': 'num_clicks',
        'name': 'Number of article clicks',
    },
    {
        'db': 'domains',
        'type': 'count',
        'template': 'count',
        'query': {},
        'id': 'num_domains',
        'name': 'Number of domains',
    },
    {
        'db': 'pages',
        'type': 'aggregate',
        'template': 'table',
        'query': [
            {
                '$match': { 'date_published': None },
            },
            {
                '$group': {
                    '_id': '$domain',
                    'total': { '$sum': 1 },
                 },
            },
            { '$sort': { 'total': -1 } },
            { '$limit': 10 },
        ]),
        'id': 'table_missing_date',
        'name': 'Pages missing date',
        'value': lambda d: d['total'],
        'xlabel': 'Domain',
        'ylabel': 'Count',
    },
]
"""    {
        'db': 'articles',
        'query': {
            'pages': None,
        },
        'id': 'num_articles_no_page',
        'name': 'Number of unscraped articles',
    },
    {
        'db': 'articles',
        'query': {
            'page.date_published': None,
        },
        'id': 'num_articles_no_date',
        'name': 'Number of articles without a date',
    },
    {
        'db': 'articles',
        'query': {
            'analysis.possible.candidates': {
                '$size': 0,
            },
        },
        'id': 'num_articles_no_candidates',
        'name': 'Number of articles with no candidates',
    },
    {
        'db': 'articles',
        'query': {
            'analysis.possible.constituencies': {
                '$size': 0,
            },
        },
        'id': 'num_articles_no_constituencies',
        'name': 'Number of articles with no constituencies',
    },
    {
        'db': 'articles',
        'query': {
            'output.tag_clash': True,
         },
        'id': 'tag_clash',
        'name': 'Number of articles with clashing tags',
    },
]"""


dashboard_query_index = {
    q['id']: q for q in dashboard_queries
}

def time_series(docs, key):
    ts = [doc[key] for doc in docs]

    ts_min = min(ts)
    ts_max = max(ts)

     
 
@app.route('/dashboard')
@login_required
def dashboard():
    stats = {}

    for query in dashboard_queries:
        db_query = db[query['db']]
   
        if query['type'] == 'count': 
            result = db_query.find(query['query']).count()
        elif query['type'] == 'aggregate':
            result = [x for x in db_query.aggregate(query['query']) if x['_id']['y'] > 2014]

        if query.get('value'):
            for d in result:
                d['value'] = query['value'](d)

        stats[query['id']] = result

    return render_template('dashboard.html',
                           queries=dashboard_queries,
                           stats=stats)


@app.route('/dashboard/articles/<query_id>')
@login_required
def dashboard_article(query_id):
    query = dashboard_query_index[query_id]
    docs = list(db_articles.find(query['query']))

    for doc in docs:
        doc['page'] = Page.get(doc['pages'][0])

    return render_template('dashboard_query.html',
                           query=query,
                           articles=docs)

@app.route('/dashboard/domains')
@login_required
def dashboard_domains():
    docs = db_domains.find().sort([('name', 1)])

    return render_template('dashboard_domains.html',
                           domains=docs)


@app.route('/dashboard/domains/<doc_id>', methods=["PUT", "POST"])
@login_required
def dashboard_domain(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_domains.find_one({'_id': doc_id})

    name = request.form.get("name")

    doc['name'] = name
    db_domains.save(doc)

    return render_template('dashboard_domain.html',
                           domain=doc) 

cache = {}

@app.route('/dashboard/classifier')
@login_required
def dashboard_classifier():
    docs = db_articles.find()

    if 'stats' not in cache:
        stats = defaultdict(Counter)

        for doc in docs:
            if 'machine' in doc.get('analysis', {}):
                timestamp = time.mktime(doc['time_added'].date().timetuple())

                stats[timestamp]['remove'] += len(doc['analysis']['machine']['candidates']['remove'])
                stats[timestamp]['confirm'] += len(doc['analysis']['machine']['candidates']['confirm'])

        stats_json = []
        for day, day_stats in sorted(stats.items()):
            day_stats = dict(day_stats)
            day_stats['day'] = day
            stats_json.append(day_stats)

        cache['stats'] = stats_json
    
    return render_template('dashboard_classifier.html',
                           stats_json=json.dumps(cache))


@app.route('/recent')
def action_log():
    log = db_action_log.find() \
                       .sort([('time_now', -1)])[:50]

    return render_template('action_log.html',
                           log=log)


@app.route('/queue')
@login_required
def moderation_queue():
    articles = list(db_articles.find({'state': 'moderated'}) \
                          .sort([('time_added', -1)])[:50])

    for doc in articles:
        if 'pages' in doc:
            doc['page'] = Page.get(doc['pages'][0])

    return render_template('moderation_queue.html',
                           articles=articles)

permitted_states = {'approved', 'removed', 'moderated'}


@app.route('/article/state', methods=['PUT'])
@login_required
def article_update_state():
    doc_id = ObjectId(request.form.get('doc_id'))
    doc = db_articles.find_one({'_id': doc_id})

    state = request.form.get('state', None)
    state_old = doc['state']

    if state in permitted_states:
        doc['state'] = state
        db_articles.save(doc)

        log(
            'update_state',
            url_for('.article', doc_id=str(doc_id)),
            {
                'state': state,
                'state_old': state_old
            }
        )
