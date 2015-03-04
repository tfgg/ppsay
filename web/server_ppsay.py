import requests
import json
from urlparse import urlparse

from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flask import Blueprint, url_for, render_template, request, jsonify, abort, redirect
from flask.ext.login import login_required, current_user

from ppsay.log import log
from ppsay.domains import domain_whitelist
from ppsay.matches import resolve_matches
from ppsay.sources import get_source
from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    get_candidate,
    get_candidates,
)

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles
db_candidates = db_client.news.candidates
db_log = db_client.news.action_log

app = Blueprint('ppsay',
                __name__,
                template_folder='templates')

def get_mapit_area(area_id):
  req = requests.get("http://mapit.mysociety.org/area/{}".format(area_id))

  return req.json()

@app.route('/')
def index():
  article_docs = db_articles.find({'state': 'approved'}) \
                            .sort([('time_added', -1)]) \
                            .limit(100)

  article_docs = [x for x in article_docs if len([y for y in x.get('candidates', []) if y['state'] != 'removed']) > 0 
                                          or len([y for y in x.get('constituencies', []) if y['state'] != 'removed']) > 0]

  return render_template('index.html',
                         constituencies=constituencies,
                         articles=article_docs)

@app.route('/articles')
def articles():
    return redirect(url_for('.index'))

@app.route('/statistics')
def statistics():
    total_candidate_mentions = db_candidates.find().sort([("mentions.total_count", -1)]).limit(50)
    last_week_candidate_mentions = db_candidates.find().sort([("mentions.last_week_count", -1)]).limit(50)

    return render_template('statistics.html',
                           total_candidate_mentions=total_candidate_mentions,
                           last_week_candidate_mentions=last_week_candidate_mentions)

@app.route('/person/<int:person_id>')
def person(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})
    
    current_party_id = None
    current_constituency_id = None

    if '2010' in person_doc['candidacies']:
        current_party_id = person_doc['candidacies']['2010']['party']['id']
        current_constituency_id = person_doc['candidacies']['2010']['constituency']['id']

    if '2015' in person_doc['candidacies']:
        current_party_id = person_doc['candidacies']['2015']['party']['id']
        current_constituency_id = person_doc['candidacies']['2015']['constituency']['id']

    article_docs = db_articles.find({'state': 'approved',
                                   'candidates': {'$elemMatch': {'id': person_id, 'state': {'$ne': 'removed'}}}}) \
                            .sort([('time_added', -1)])

    article_docs = list(article_docs)

    for article_doc in article_docs:
        for quote_doc in article_doc['quotes']:
            score = 0.0

            if person_id in [x[0] for x in quote_doc['candidate_ids']]:
                score += 1.0
            
            if current_constituency_id in [x[0] for x in quote_doc['constituency_ids']]:
                score += 0.5
           
            score += len(quote_doc['candidate_ids']) * 0.1
            score += len(quote_doc['constituency_ids']) * 0.1
 
            print score
            quote_doc['score'] = score

        article_doc['quotes'] = sorted(article_doc['quotes'], key=lambda x: x['score'], reverse=True)

    return render_template('person.html',
                           articles=article_docs,
                           person=person_doc)

@app.route('/constituency/<int:constituency_id>')
def constituency(constituency_id):
    candidate_docs = db_candidates.find({'deleted': {'$ne': True},
                                       '$or': [{"candidacies.2010.constituency.id": str(constituency_id)},
                                               {"candidacies.2015.constituency.id": str(constituency_id)}]})

    candidate_docs = sorted(candidate_docs, key=lambda x: x['name'])

    candidate_ids = [x['id'] for x in candidate_docs if ('2015' in x['candidacies'] and x['candidacies']['2015']['constituency']['id'] == str(constituency_id)) \
                                                       or x['incumbent']]

    article_docs = db_articles.find({'state': 'approved',
                                   '$or': [{'constituencies': {'$elemMatch': {'id': str(constituency_id), 'state': {'$ne': 'removed'}}}},
                                           {'candidates': {'$elemMatch': {'id': {'$in': candidate_ids}, 'state': {'$ne': 'removed'}}}}]}) \
                            .sort([["time_added", -1]])

    article_docs = list(article_docs)
    for article_doc in article_docs:
        for quote_doc in article_doc['quotes']:
            score = 0.0

            for candidate_id in candidate_ids:
                if candidate_id in [x[0] for x in quote_doc['candidate_ids']]:
                    score += 0.5

            if str(constituency_id) in [x[0] for x in quote_doc['constituency_ids']]:
                score += 1.0
           
            score += len(quote_doc['candidate_ids']) * 0.1
            score += len(quote_doc['constituency_ids']) * 0.1
 
            print score
            quote_doc['score'] = score

        article_doc['quotes'] = sorted(article_doc['quotes'], key=lambda x: x['score'], reverse=True)

        if article_doc['page']['date_published']:
            article_doc['order_date'] = article_doc['page']['date_published']
        else:
            article_doc['order_date'] = article_doc['time_added']

    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    area_doc = get_mapit_area(constituency_id)
    area_doc['id'] = str(area_doc['id'])

    return render_template('constituency.html',
                           articles=article_docs,
                           candidates=candidate_docs,
                           area=area_doc)

@app.route('/article', methods=['POST'])
def article_add():
    url = request.form.get('url', None)

    if url is None:
        return abort(500, "URL of article not supplied")

    if current_user.is_authenticated():
        user_name = current_user['user_name']
    else:
        user_name = "anonymous"

    article_doc = get_source(url, 'user/' + user_name, 'moderated')
    
    log('article_add', url_for('.article', doc_id=str(article_doc['_id'])), {'url': url,})

    url_parsed = urlparse(url)

    if url_parsed.netloc in domain_whitelist:
        article_doc['state'] = 'approved'
        db_articles.save(article_doc)
    
    return redirect(url_for(".article", doc_id=str(article_doc['_id'])))


@app.route('/article/<doc_id>')
@login_required
def article(doc_id):
    doc_id = ObjectId(doc_id)

    doc = db_articles.find_one({'_id': doc_id})

    return render_template('article.html',
                           article=doc)

@app.route('/article/<doc_id>/people', methods=['PUT'])
@login_required
def article_person_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})

    person_id = request.form.get('person_id', None)

    doc['user']['candidates']['confirm'].append(person_id)

    if person_id in doc['user']['candidates']['remove']:
        doc['user']['candidates']['remove'].remove(person_id)
    
    doc['user']['candidates']['confirm'] = list(set(doc['user']['candidates']['confirm']))
    doc['user']['candidates']['remove'] = list(set(doc['user']['candidates']['remove']))
   
    resolve_matches(doc)
 
    db_articles.save(doc)

    log('person_confirm', url_for('.article', doc_id=str(doc_id)), {'person_id': person_id,
                                                                   'person_name': get_candidate(person_id)['name']})
 
    return render_template('article_people_tagged.html',
                           article=doc)
 
@app.route('/article/<doc_id>/people', methods=['DELETE'])
@login_required
def article_person_remove(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})
    
    person_id = request.form.get('person_id', None)

    doc['user']['candidates']['remove'].append(person_id)
    
    if person_id in doc['user']['candidates']['confirm']:
        doc['user']['candidates']['confirm'].remove(person_id)
    
    doc['user']['candidates']['confirm'] = list(set(doc['user']['candidates']['confirm']))
    doc['user']['candidates']['remove'] = list(set(doc['user']['candidates']['remove']))

    resolve_matches(doc)

    db_articles.save(doc)
    
    log('person_remove', url_for('.article', doc_id=str(doc_id)), {'person_id': person_id, 
                                                                  'person_name': get_candidate(person_id)['name']})
 
    return render_template('article_people_tagged.html',
                           article=doc)

@app.route('/article/<doc_id>/constituencies', methods=['PUT'])
@login_required
def article_constituency_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})

    constituency_id = request.form.get('constituency_id', None)

    doc['user']['constituencies']['confirm'].append(constituency_id)

    if constituency_id in doc['user']['constituencies']['remove']:
        doc['user']['constituencies']['remove'].remove(constituency_id)
    
    doc['user']['constituencies']['confirm'] = list(set(doc['user']['constituencies']['confirm']))
    doc['user']['constituencies']['remove'] = list(set(doc['user']['constituencies']['remove']))
    
    resolve_matches(doc)

    db_articles.save(doc)
    
    log('constituency_confirm', url_for('.article', doc_id=str(doc_id)), {'constituency_id': constituency_id,
                                                                         'constituency_name': constituencies_index[constituency_id]['name']})
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)
 
@app.route('/article/<doc_id>/constituencies', methods=['DELETE'])
@login_required
def article_constituency_remove(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})

    constituency_id = request.form.get('constituency_id', None)

    doc['user']['constituencies']['remove'].append(constituency_id)

    if constituency_id in doc['user']['constituencies']['confirm']:
        doc['user']['constituencies']['confirm'].remove(constituency_id)
    
    doc['user']['constituencies']['confirm'] = list(set(doc['user']['constituencies']['confirm']))
    doc['user']['constituencies']['remove'] = list(set(doc['user']['constituencies']['remove']))
    
    resolve_matches(doc)

    db_articles.save(doc)
    
    log('constituency_remove', url_for('.article', doc_id=str(doc_id)), {'constituency_id': constituency_id,
                                                                        'constituency_name': constituencies_index[constituency_id]['name']})
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)

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

        log('update_state', url_for('.article', doc_id=str(doc_id)), {'state': state,
                                                                     'state_old': state_old})

@app.route('/autocomplete/person', methods=['GET'])
def autocomplete_person():
    partial_person_name = request.args.get('term')

    matches = []
    for candidate in get_candidates():
        if candidate['name'].lower().startswith(partial_person_name.lower()):
            party = constituency = 'Unknown'

            if '2015' in candidate['candidacies']:
                party = candidate['candidacies']['2015']['party']['name']
                constituency = candidate['candidacies']['2015']['constituency']['name']
            elif '2010' in candidate['candidacies']:
                party = candidate['candidacies']['2010']['party']['name']
                constituency = candidate['candidacies']['2010']['constituency']['name']

            label = u"{} ({}) - {}".format(candidate['name'], party, constituency)
            matches.append({'label': label, 'value': candidate['id']})

    return json.dumps(matches)

@app.route('/autocomplete/constituency', methods=['GET'])
def autocomplete_constituency():
    partial_constituency_name = request.args.get('term')

    matches = []
    for constituency_id, names in constituencies_names.items():
        for name in names:
            if name.lower().startswith(partial_constituency_name.lower()):
                matches.append({'label': name, 'value': constituency_id})

    return json.dumps(matches)

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

@app.route('/recent')
def action_log():
    log = db_log.find() \
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

