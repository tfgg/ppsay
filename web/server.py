import requests
import json
from bson import ObjectId
from pymongo import MongoClient
from flask import Flask, url_for, render_template, request, jsonify

from ppsay.matches import resolve_matches
from ppsay.data import (
    constituencies,
    candidates,
    constituencies_names
)

db_client = MongoClient()

articles = db_client.news.articles

app = Flask(__name__)

def get_person(person_id):
  req = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(person_id))

  return req.json()['result']

def get_mapit_area(area_id):
  req = requests.get("http://mapit.mysociety.org/area/{}".format(area_id))

  return req.json()

@app.route('/')
def index():
  article_docs = articles.find() \
                         .sort([('page.date_published', -1)])

  return render_template('index.html',
                         articles=article_docs)

@app.route('/person/<int:person_id>')
def person(person_id):
  article_docs = articles.find({'candidates':
                                {'$elemMatch': {'id': str(person_id)}}}) \
                         .sort([('page.date_published', -1)])

  person_doc = get_person(person_id)

  person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('person.html',
                         articles=article_docs,
                         person=person_doc)

@app.route('/constituency/<int:constituency_id>')
def constituency(constituency_id):
  article_docs = articles.find({'constituencies':
                                {'$elemMatch': {'id': str(constituency_id), 'state': {'$ne': 'removed'}}}}) \
                         .sort([('page.date_published', -1)])

  area_doc = get_mapit_area(constituency_id)
  #posts_doc = get_person(person_id)

  #person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('constituency.html',
                         articles=article_docs,
                         area=area_doc)

@app.route('/article/<doc_id>')
def article(doc_id):
    doc_id = ObjectId(doc_id)

    doc = articles.find_one({'_id': doc_id})

    return render_template('article.html',
                           article=doc)

@app.route('/article/<doc_id>/people', methods=['PUT'])
def article_person_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    doc = articles.find_one({'_id': doc_id})

    person_id = request.form.get('person_id', None)

    doc['user']['candidates']['confirm'].append(person_id)

    if person_id in doc['user']['candidates']['remove']:
        doc['user']['candidates']['remove'].remove(person_id)
    
    doc['user']['candidates']['confirm'] = list(set(doc['user']['candidates']['confirm']))
    doc['user']['candidates']['remove'] = list(set(doc['user']['candidates']['remove']))
   
    resolve_matches(doc)
 
    articles.save(doc)
 
    return render_template('article_people_tagged.html',
                           article=doc)
 
@app.route('/article/<doc_id>/people', methods=['DELETE'])
def article_person_remove(doc_id):
    doc_id = ObjectId(doc_id)
    doc = articles.find_one({'_id': doc_id})
    
    person_id = request.form.get('person_id', None)

    doc['user']['candidates']['remove'].append(person_id)
    
    if person_id in doc['user']['candidates']['confirm']:
        doc['user']['candidates']['confirm'].remove(person_id)
    
    doc['user']['candidates']['confirm'] = list(set(doc['user']['candidates']['confirm']))
    doc['user']['candidates']['remove'] = list(set(doc['user']['candidates']['remove']))

    resolve_matches(doc)

    articles.save(doc)
 
    return render_template('article_people_tagged.html',
                           article=doc)

@app.route('/article/<doc_id>/constituencies', methods=['PUT'])
def article_constituency_confirm(doc_id):
    doc_id = ObjectId(doc_id)
    doc = articles.find_one({'_id': doc_id})

    constituency_id = request.form.get('constituency_id', None)

    doc['user']['constituencies']['confirm'].append(constituency_id)

    if constituency_id in doc['user']['constituencies']['remove']:
        doc['user']['constituencies']['remove'].remove(constituency_id)
    
    doc['user']['constituencies']['confirm'] = list(set(doc['user']['constituencies']['confirm']))
    doc['user']['constituencies']['remove'] = list(set(doc['user']['constituencies']['remove']))
    
    resolve_matches(doc)

    articles.save(doc)
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)
 
@app.route('/article/<doc_id>/constituencies', methods=['DELETE'])
def article_constituency_remove(doc_id):
    doc_id = ObjectId(doc_id)
    doc = articles.find_one({'_id': doc_id})

    constituency_id = request.form.get('constituency_id', None)

    doc['user']['constituencies']['remove'].append(constituency_id)

    if constituency_id in doc['user']['constituencies']['confirm']:
        doc['user']['constituencies']['confirm'].remove(constituency_id)
    
    doc['user']['constituencies']['confirm'] = list(set(doc['user']['constituencies']['confirm']))
    doc['user']['constituencies']['remove'] = list(set(doc['user']['constituencies']['remove']))
    
    resolve_matches(doc)

    articles.save(doc)
 
    return render_template('article_constituencies_tagged.html',
                           article=doc)

@app.route('/autocomplete/person', methods=['GET'])
def autocomplete_person():
    partial_person_name = request.args.get('term')

    matches = []
    for candidate in candidates:
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
def dashboard():
    stats = {query['id']: articles.find(query['query']).count() for query in dashboard_queries}

    return render_template('dashboard.html',
                           queries=dashboard_queries,
                           stats=stats)

@app.route('/dashboard/articles/<query_id>')
def dashboard_article(query_id):
    query = dashboard_query_index[query_id]
    docs = articles.find(query['query'])

    return render_template('dashboard_query.html',
                           query=query,
                           articles=docs)

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)

