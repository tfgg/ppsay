from collections import Counter, defaultdict

from bson import ObjectId

from flask import (
    Blueprint,
    render_template,
    request,
)

from flask.ext.login import login_required

from ppsay.db import (
    db_articles,
    db_action_log,
    db_domains,
)

app = Blueprint('dashboard',
                __name__,
                template_folder='templates')

dashboard_queries = [{'query': {},
                      'id': 'num_articles',
                      'name': 'Number of articles',},
                     {'query': {'page': None},
                      'id': 'num_articles_no_page',
                      'name': 'Number of unscraped articles',},
                     {'query': {'page.date_published': None},
                      'id': 'num_articles_no_date',
                      'name': 'Number of articles without a date',},
                     {'query': {'possible.candidates': {'$size': 0}},
                      'id': 'num_articles_no_candidates',
                      'name': 'Number of articles with no candidates',},
                     {'query': {'possible.constituencies': {'$size': 0}},
                      'id': 'num_articles_no_constituencies',
                      'name': 'Number of articles with no constituencies',},
                     {'query': {'tag_clash': True},
                      'id': 'tag_clash',
                      'name': 'Number of articles with clashing tags',}
                    ]


dashboard_query_index = {q['id']: q for q in dashboard_queries}
          

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {query['id']: db_articles.find(query['query']).count() for query in dashboard_queries}

    return render_template('dashboard.html',
                           queries=dashboard_queries,
                           stats=stats)


@app.route('/dashboard/articles/<query_id>')
@login_required
def dashboard_article(query_id):
    query = dashboard_query_index[query_id]
    docs = db_articles.find(query['query'])

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


@app.route('/dashboard/classifier')
@login_required
def dashboard_classifier():
    docs = list(db_articles.find())

    stats = defaultdict(Counter)

    for doc in docs:
        for candidate in doc['candidates']:
            stats[doc['time_added'].date()][candidate['state']] += 1

    stats = sorted(stats.items())

    return render_template('dashboard_classifier.html',
                           stats=stats) 


@app.route('/recent')
def action_log():
    log = db_action_log.find() \
                       .sort([('time_now', -1)])[:50]

    return render_template('action_log.html',
                           log=log)


@app.route('/queue')
@login_required
def moderation_queue():
    articles = db_articles.find({'state': 'moderated'}) \
                          .sort([('time_added', -1)])[:50]

    return render_template('moderation_queue.html',
                           articles=articles)

