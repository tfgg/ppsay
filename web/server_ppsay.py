# -*- coding: utf-8 -*-
import requests
import json
import math
import iso8601
import pytz

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
from ppsay.page import Page
from ppsay.article import Article

from ppsay.constituency import (
    constituency_get_candidates,
    filter_candidate_or_incumbent,
)

from ppsay.data import (
    get_constituencies,
    get_constituency,
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

from ppsay.stream import StreamItem

app = Blueprint('ppsay',
                __name__,
                template_folder='templates')


def get_mapit_area(area_id):
    req = requests.get("http://mapit.mysociety.org/area/{}".format(area_id))

    return req.json()


@app.route('/')
def index():
    stream = StreamItem.get_all(100) 

    last_week_candidate_mentions = db_candidates.find().sort([("mentions.last_week_count", -1)]).limit(6)

    return render_template('index.html',
                           constituencies=db_areas.find().sort([('name', 1)]),
                           stream=stream,
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


@app.route('/person/<int:person_id>/articles')
def person_articles(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    stream = StreamItem.get_by_entities(None, [person_id], None)

    return render_template('person.html',
                           stream=stream,
                           person=person_doc)


@app.route('/person/<int:person_id>/quotes')
def person_quotes(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    quote_docs = []#get_person_quotes(person_id)

    return render_template('person_quotes.html',
                           person=person_doc,
                           quotes=quote_docs)


def get_person_stats(stream):
    if len(stream) == 0:
        return [], []

    weekly_buckets = sorted(list(Counter(
        item.date_order.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=item.date_order.weekday())
        for item in stream
    ).items()))

    date_now = datetime.now(pytz.UTC)
    months = [
        datetime(year,month,1,tzinfo=pytz.UTC)
        for year in range(2015,date_now.year+1)
        for month in range(1,13)
        if datetime(year,month,1,tzinfo=pytz.UTC) <= stream[0].date_order
    ]

    years = [
        datetime(year,1,1,tzinfo=pytz.UTC)
        for year in range(2015,date_now.year+1)
    ]

    return weekly_buckets, months, years


def get_person_domains(stream):
    return sorted(
        [
            (get_domain(domain), count)
            for domain, count in Counter(item.data['domain'] for item in stream).items()
        ],
        key=lambda x: x[1],
        reverse=True,
    )


@app.route('/person/<int:person_id>')
def person(person_id):
    person_id = str(person_id)
    person_doc = db_candidates.find_one({'id': person_id})

    now = datetime.now(pytz.UTC)
    person_doc['current_election'] = None

    for election_id in person_doc['candidacies']:
        if elections[election_id]['date'] > now:
            elections[election_id]['current'] = True
            person_doc['current_election'] = election_id
        else:
            elections[election_id]['current'] = False

    past_elections = sorted([elections[election_id] for election_id in person_doc['candidacies'] if not elections[election_id]['current']], key=lambda x: x['date'], reverse=True)
    if len(past_elections) > 0:
        person_doc['last_election'] = past_elections[0]['id'].replace('.', '_')
    else:
        person_doc['last_election'] = None

    stream = StreamItem.get_by_entities(None, [person_id], None) 

    weekly_buckets, months, years = get_person_stats(stream)
    domains = get_person_domains(stream)

    person_doc['candidacies_sorted'] = sorted(person_doc['candidacies'].items(), key=lambda x: elections[x[1]['election_id'].replace('.','_')]['date'],reverse=True)

    return render_template('person.html',
                           person=person_doc,
                           quotes=[],#quote_docs,
                           stream=stream[:100],
                           elections=elections,
                           domains=domains,
                           weekly_buckets=weekly_buckets,
                           year_2015=datetime(2015,1,1,tzinfo=pytz.UTC),
                           today=datetime.now(pytz.UTC),
                           months=months,
                           years=years)


@app.route('/constituency/<constituency_id>.xml')
def constituency_rss(constituency_id):
    resp =  make_response(constituency(constituency_id, rss=True))
    resp.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    
    return resp


@app.route('/constituency/<constituency_id>')
def constituency(constituency_id, rss=False):
    constituency_id = str(constituency_id)

    candidate_docs = constituency_get_candidates(constituency_id)
    person_ids = filter_candidate_or_incumbent(candidate_docs, constituency_id)

    stream = StreamItem.get_by_entities(100, person_ids, [constituency_id]) 

    area_doc = get_mapit_area(constituency_id)
    area_doc['id'] = str(area_doc['id'])

    if rss:
        return render_template('constituency_rss.xml',
                               stream=stream,
                               candidates=candidate_docs,
                               area=area_doc)
    else:
        return render_template('constituency.html',
                               stream=stream,
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
    article = Article.get_by_id(doc_id)

    person_id = request.form.get('person_id', None)

    article.analysis['user']['candidates']['confirm'].append(person_id)

    if person_id in article.analysis['user']['candidates']['remove']:
        article.analysis['user']['candidates']['remove'].remove(person_id)
    
    article.analysis['user']['candidates']['confirm'] = list(set(article.analysis['user']['candidates']['confirm']))
    article.analysis['user']['candidates']['remove'] = list(set(article.analysis['user']['candidates']['remove']))
  
    article.process()
    article.save() 

    log('person_confirm', url_for('.article', doc_id=str(doc_id)), {'person_id': person_id,
                                                                   'person_name': get_candidate(person_id)['name']})
 
    return render_template(
        'article_people_tagged.html',
        article=article,
    )
 

@app.route('/article/<doc_id>/people', methods=['DELETE'])
@login_required
def article_person_remove(doc_id):
    doc_id = ObjectId(doc_id)
    article = Article.get_by_id(doc_id)
    
    person_id = request.form.get('person_id', None)

    article.analysis['user']['candidates']['remove'].append(person_id)
    
    if person_id in article.analysis['user']['candidates']['confirm']:
        article.analysis['user']['candidates']['confirm'].remove(person_id)
    
    article.analysis['user']['candidates']['confirm'] = list(set(article.analysis['user']['candidates']['confirm']))
    article.analysis['user']['candidates']['remove'] = list(set(article.analysis['user']['candidates']['remove']))

    article.process()
    article.save() 
    
    log('person_remove', url_for('.article', doc_id=str(doc_id)), {'person_id': person_id, 
                                                                  'person_name': get_candidate(person_id)['name']})
 
    return render_template('article_people_tagged.html',
                           article=article)


@app.route('/article/<doc_id>/constituencies', methods=['PUT'])
@login_required
def article_constituency_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    article = Article.get_by_id(doc_id)

    constituency_id = request.form.get('constituency_id', None)

    article.analysis['user']['constituencies']['confirm'].append(constituency_id)

    if constituency_id in article.analysis['user']['constituencies']['remove']:
        article.analysis['user']['constituencies']['remove'].remove(constituency_id)
    
    article.analysis['user']['constituencies']['confirm'] = list(set(article.analysis['user']['constituencies']['confirm']))
    article.analysis['user']['constituencies']['remove'] = list(set(article.analysis['user']['constituencies']['remove']))
    
    article.process()
    article.save()
    
    log(
        'constituency_confirm',
        url_for('.article', doc_id=str(doc_id)),
        {
            'constituency_id': constituency_id,
            'constituency_name': get_constituency(constituency_id)['name'],
        }
    )
 
    return render_template('article_constituencies_tagged.html',
                           article=article)


@app.route('/article/<doc_id>/constituencies', methods=['DELETE'])
@login_required
def article_constituency_remove(doc_id):
    doc_id = ObjectId(doc_id)
    article = Article.get_by_id(doc_id)

    constituency_id = request.form.get('constituency_id', None)

    article.analysis['user']['constituencies']['remove'].append(constituency_id)

    if constituency_id in article.analysis['user']['constituencies']['confirm']:
        article.analysis['user']['constituencies']['confirm'].remove(constituency_id)
    
    article.analysis['user']['constituencies']['confirm'] = list(set(article.analysis['user']['constituencies']['confirm']))
    article.analysis['user']['constituencies']['remove'] = list(set(article.analysis['user']['constituencies']['remove']))
    
    article.process()
    article.save()
    
    log(
        'constituency_remove', 
        url_for('.article', doc_id=str(doc_id)), 
        {
            'constituency_id': constituency_id,
            'constituency_name': get_constituency(constituency_id)['name'],
        }
    )
 
    return render_template('article_constituencies_tagged.html',
                           article=article)


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

