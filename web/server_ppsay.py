# -*- coding: utf-8 -*-
import requests
import json
import math
import iso8601

from datetime import timedelta, datetime

from collections import Counter
from urlparse import urlparse
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
from flask.ext.login import login_required, current_user

from ppsay.log import log
from ppsay.domains import domain_whitelist, get_domain
from ppsay.matches import resolve_matches
from ppsay.sources import get_source
from ppsay.article import get_articles
from ppsay.page import Page

from ppsay.constituency import (
    constituency_get_candidates,
    filter_candidate_or_incumbent,
)

from ppsay.data import (
    get_constituencies,
    get_candidate,
    get_candidates,
    elections
)

from ppsay.db import (
    db_articles,
    db_candidates,
    db_action_log,
    db_domains,
    db_events,
    db_areas
)

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

    show_hidden = request.args.get('hidden', None)

    if show_hidden is not None:
        article_docs = list(article_docs)
    else:
        article_docs = [
            x for x in article_docs
            if sum(
                1 for y in x['analysis']['final'].get('candidates', [])
                if y['state'] not in ['removed', 'removed_ml']
            ) > 0
        ]

    for article_doc in article_docs:
        article_doc['election'] = 'ge2015'
        article_doc['page'] = Page.get(article_doc['pages'][0])

    last_week_candidate_mentions = db_candidates.find().sort([("mentions.last_week_count", -1)]).limit(5)

    return render_template('index.html',
                           constituencies=db_areas.find().sort([('name', 1)]),
                           articles=article_docs,
                           last_week_candidate_mentions=last_week_candidate_mentions)


@app.route('/articles')
def articles():
    return redirect(url_for('.index'))


@app.route('/statistics')
def statistics():
    total_candidate_mentions = db_candidates.find().sort([("mentions.total_count", -1)]).limit(50)
    last_week_candidate_mentions = db_candidates.find().sort([("mentions.last_week_count", -1)]).limit(50)

    loc_nat_candidates = list(db_candidates.find())

    for candidate in loc_nat_candidates:
        total = float(candidate['mentions']['national_count'] + candidate['mentions']['local_count'])
        candidate['mentions']['nat_ratio'] = (candidate['mentions']['national_count'] / (total + 1) - 0.5) * math.sqrt(total)
        candidate['mentions']['loc_ratio'] = (candidate['mentions']['local_count'] / (total + 1) - 0.5) * math.sqrt(total)

    local_candidate_mentions = sorted(loc_nat_candidates, key=lambda x: x['mentions']['loc_ratio'], reverse=True)[:50] 
    national_candidate_mentions = sorted(loc_nat_candidates, key=lambda x: x['mentions']['nat_ratio'], reverse=True)[:50] 

    return render_template(
        'statistics.html',
        total_candidate_mentions=total_candidate_mentions,
        last_week_candidate_mentions=last_week_candidate_mentions,
        national_candidate_mentions=national_candidate_mentions,
        local_candidate_mentions=local_candidate_mentions
    )


@app.route('/statistics.json')
def statistics_json():
    total_candidate_mentions = list(db_candidates.find().sort([("mentions.total_count", -1)]))
    last_week_candidate_mentions = list(db_candidates.find().sort([("mentions.last_week_count", -1)]))

    total_mentions = sum(
        x['mentions']['total_count'] for x in total_candidate_mentions if 'mentions' in x
    )

    last_week_mentions = sum(
        x['mentions']['last_week_count'] for x in last_week_candidate_mentions if 'mentions' in x
    )

    num_candidates = sum(
        1 for x in total_candidate_mentions if 'mentions' in x and x['mentions']['total_count'] > 0
    )

    return jsonify({
        'candidates': {
            'total_mentions': total_mentions,
            'last_week_mentions': last_week_mentions,
            'num_candidates': num_candidates,
        }
    })


def get_person_articles(person_id):
    person_doc = db_candidates.find_one({'id': person_id})

    if 'ge2015' in person_doc['candidacies']:
        current_party_id = person_doc['candidacies']['ge2015']['party']['id']
        current_constituency_id = person_doc['candidacies']['ge2015']['constituency']['id']

    elif 'ge2010' in person_doc['candidacies']:
        current_party_id = person_doc['candidacies']['ge2010']['party']['id']
        current_constituency_id = person_doc['candidacies']['ge2010']['constituency']['id']

    else:
        current_party_id = None
        current_constituency_id = None

    article_docs = list(get_articles([person_id]))

    for article_doc in article_docs:
        for quote_doc in article_doc['output']['quotes']:
            score = 0.0

            if person_id in [x[0] for x in quote_doc['candidate_ids']]:
                score += 10.0
            
            if current_constituency_id in [x[0] for x in quote_doc['constituency_ids']]:
                score += 0.5
           
            score += len(quote_doc['candidate_ids']) * 0.1
            score += len(quote_doc['constituency_ids']) * 0.1
 
            quote_doc['score'] = score
        
        article_doc['output']['quotes'] = sorted(article_doc['output']['quotes'], key=lambda x: x['score'], reverse=True)
 
    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    return article_docs


@app.route('/person/<int:person_id>/articles')
def person_articles(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    article_docs = get_person_articles(person_id)

    return render_template('person.html',
                           articles=article_docs,
                           person=person_doc)


def get_person_quotes(person_id):
    article_docs = list(get_articles([person_id]))

    quote_docs = []

    interesting_words = [
        'said', 'called', 'called on', 'says', 'promised', 'gaffe', 'popular',
        'mp', 'becoming', 'was', 'is', 'is the', 'worked', 'minister', 'councillor', 'hate', 'love',
        'university', 'children', 'family', 'wife', 'husband', 'daughter', 'son', 'married',
        'apologised', 'apology', 'tackle', 'fix', 'moral', 'ethical', 'penalty', 'law',
        'responsible', 'pledge', 'urge', 'petition', 'received', u'£', 'leader',
    ]
    
    # Use dict to remove dupes
    quote_docs = {}

    for article_doc in article_docs:
        for quote_doc in article_doc['output']['quotes']:
            if person_id in [x[0] for x in quote_doc['candidate_ids']]:
                quote_doc['article'] = article_doc

                score = 0.0
                for word in interesting_words:
                    if word in quote_doc['text'].lower():
                        score += 1.0
                
                quote_doc['article'] = article_doc
                quote_doc['score'] = score
                quote_docs[quote_doc['html']] = quote_doc

    quote_docs = sorted(quote_docs.values(), key=lambda x: x['score'], reverse=True)

    return quote_docs


@app.route('/person/<int:person_id>/quotes')
def person_quotes(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    quote_docs = get_person_quotes(person_id)

    return render_template('person_quotes.html',
                           person=person_doc,
                           quotes=quote_docs)


@app.route('/person/<int:person_id>')
def person(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    quote_docs = get_person_quotes(person_id)
    article_docs = get_person_articles(person_id)

    domains = sorted([(get_domain(domain), count) for domain, count in Counter(doc['page'].domain for doc in article_docs).items()], key=lambda x: x[1], reverse=True)

    weekly_buckets = sorted(list(Counter(doc['order_date'].replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=doc['order_date'].weekday()) for doc in article_docs).items()))

    months = [datetime(2015,i,1) for i in range(1,datetime.now().month+1)]

    return render_template('person.html',
                           person=person_doc,
                           quotes=quote_docs,
                           articles=article_docs,
                           elections=elections,
                           domains=domains,
                           weekly_buckets=weekly_buckets,
                           year_2015=datetime(2015,1,1),
                           today=datetime.now(),
                           months=months)


@app.route('/constituency/<int:constituency_id>.xml')
def constituency_rss(constituency_id):
    resp =  make_response(constituency(constituency_id, rss=True))
    resp.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    
    return resp


@app.route('/constituency/<int:constituency_id>')
def constituency(constituency_id, rss=False):
    constituency_id = str(constituency_id)

    candidate_docs = constituency_get_candidates(constituency_id)
    person_ids = filter_candidate_or_incumbent(candidate_docs, constituency_id)

    article_docs = get_articles(person_ids, [constituency_id])

    for article_doc in article_docs:
        for quote_doc in article_doc['output']['quotes']:
            score = 0.0

            for person_id in person_ids:
                if person_id in [x[0] for x in quote_doc['candidate_ids']]:
                    score += 0.5

            if str(constituency_id) in [x[0] for x in quote_doc['constituency_ids']]:
                score += 10.0
           
            score += len(quote_doc['candidate_ids']) * 0.1
            score += len(quote_doc['constituency_ids']) * 0.1
 
            quote_doc['score'] = score

        article_doc['output']['quotes'] = sorted(article_doc['output']['quotes'], key=lambda x: x['score'], reverse=True)

    if not rss:
        article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)
    else:
        article_docs = sorted(article_docs, key=lambda x: x['time_added'], reverse=True)

    area_doc = get_mapit_area(constituency_id)
    area_doc['id'] = str(area_doc['id'])

    if rss:
        return render_template('constituency_rss.xml',
                               articles=article_docs,
                               candidates=candidate_docs,
                               area=area_doc)
    else:
        return render_template('constituency.html',
                               articles=article_docs,
                               candidates=candidate_docs,
                               area=area_doc)


@app.route('/article', methods=['POST'])
def article_add():
    url = request.form.get('url', None)

    if url is None:
        return abort(500, "URL of article not supplied")

    if current_user.is_anonymous():
        user_name = "anonymous"
    else:
        user_name = current_user['user_name']

    article_doc = get_source(url, 'user/' + user_name, 'moderated')
    
    log('article_add', url_for('.article', doc_id=str(article_doc['_id'])), {'url': url,})

    url_parsed = urlparse(url)

    if url_parsed.netloc in domain_whitelist:
        article_doc['state'] = 'approved'
        db_articles.save(article_doc)

    if current_user.is_anonymous(): 
        return render_template('article_add_thanks.html',
                               article=article_doc)
    else:
        return redirect(url_for(".article", doc_id=str(article_doc['_id'])))


@app.route('/article/<doc_id>')
@login_required
def article(doc_id):
    doc_id = ObjectId(doc_id)

    doc = db_articles.find_one({'_id': doc_id})

    doc['page'] = Page.get(doc['pages'][0])

    return render_template('article.html',
                           article=doc)

def _resolve_matches(doc):
    page = Page.get(doc['pages'][0])

    texts = [page.text, page.title,]

    resolve_matches(texts, doc)

@app.route('/article/<doc_id>/people', methods=['PUT'])
@login_required
def article_person_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})

    person_id = request.form.get('person_id', None)

    doc['analysis']['user']['candidates']['confirm'].append(person_id)

    if person_id in doc['analysis']['user']['candidates']['remove']:
        doc['analysis']['user']['candidates']['remove'].remove(person_id)
    
    doc['analysis']['user']['candidates']['confirm'] = list(set(doc['analysis']['user']['candidates']['confirm']))
    doc['analysis']['user']['candidates']['remove'] = list(set(doc['analysis']['user']['candidates']['remove']))
   
    _resolve_matches(doc)
 
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

    doc['analysis']['user']['candidates']['remove'].append(person_id)
    
    if person_id in doc['analysis']['user']['candidates']['confirm']:
        doc['analysis']['user']['candidates']['confirm'].remove(person_id)
    
    doc['analysis']['user']['candidates']['confirm'] = list(set(doc['analysis']['user']['candidates']['confirm']))
    doc['analysis']['user']['candidates']['remove'] = list(set(doc['analysis']['user']['candidates']['remove']))

    _resolve_matches(doc)

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

    doc['analysis']['user']['constituencies']['confirm'].append(constituency_id)

    if constituency_id in doc['analysis']['user']['constituencies']['remove']:
        doc['analysis']['user']['constituencies']['remove'].remove(constituency_id)
    
    doc['analysis']['user']['constituencies']['confirm'] = list(set(doc['analysis']['user']['constituencies']['confirm']))
    doc['analysis']['user']['constituencies']['remove'] = list(set(doc['analysis']['user']['constituencies']['remove']))
    
    _resolve_matches(doc)

    db_articles.save(doc)
    
    log(
        'constituency_confirm',
        url_for('.article', doc_id=str(doc_id)),
        {
            'constituency_id': constituency_id,
            'constituency_name': get_constituency(constituency_id)['name'],
        }
    )
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)


@app.route('/article/<doc_id>/constituencies', methods=['DELETE'])
@login_required
def article_constituency_remove(doc_id):
    doc_id = ObjectId(doc_id)
    doc = db_articles.find_one({'_id': doc_id})

    constituency_id = request.form.get('constituency_id', None)

    doc['analysis']['user']['constituencies']['remove'].append(constituency_id)

    if constituency_id in doc['user']['constituencies']['confirm']:
        doc['analysis']['user']['constituencies']['confirm'].remove(constituency_id)
    
    doc['analysis']['user']['constituencies']['confirm'] = list(set(doc['analysis']['user']['constituencies']['confirm']))
    doc['analysis']['user']['constituencies']['remove'] = list(set(doc['analysis']['user']['constituencies']['remove']))
    
    _resolve_matches(doc)

    db_articles.save(doc)
    
    log(
        'constituency_remove', 
        url_for('.article', doc_id=str(doc_id)), 
        {
            'constituency_id': constituency_id,
            'constituency_name': constituencies_index[constituency_id]['name'],
        }
    )
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)


@app.route('/autocomplete/person', methods=['GET'])
def autocomplete_person():
    partial_person_name = request.args.get('term')

    matches = []
    for candidate in get_candidates():
        if candidate['name'].lower().startswith(partial_person_name.lower()):
            party = constituency = 'Unknown'

            if 'ge2015' in candidate['candidacies']:
                party = candidate['candidacies']['ge2015']['party']['name']
                constituency = candidate['candidacies']['ge2015']['constituency']['name']
            elif 'ge2010' in candidate['candidacies']:
                party = candidate['candidacies']['ge2010']['party']['name']
                constituency = candidate['candidacies']['ge2010']['constituency']['name']

            label = u"{} ({}) - {}".format(candidate['name'], party, constituency)
            matches.append({'label': label, 'value': candidate['id']})

    return json.dumps(matches)


@app.route('/autocomplete/constituency', methods=['GET'])
def autocomplete_constituency():
    partial_constituency_name = request.args.get('term')

    matches = []
    for constituency in get_constituencies():
        for name in [constituency['name']] + constituency['other_names']:
            if name.lower().startswith(partial_constituency_name.lower()):
                matches.append({'label': name, 'value': constituency['id']})

    return json.dumps(matches)

@app.route('/event/click', methods=['POST'])
def event_click():
    doc_id = ObjectId(request.form.get('doc_id', None))
    url = request.form.get('url', None)
    href = request.form.get('href', None)
    server_time = datetime.now()
    client_time = iso8601.parse_date(request.form.get('time', None))

    doc = {
        'event': 'article_click',
        'url': url,
        'value': {
            'href': href,
            'doc_id': doc_id,
        },
        'time_server': server_time,
        'time_client': client_time,
        'client_ip': request.remote_addr,
    }

    db_events.save(doc)

    return "" 

