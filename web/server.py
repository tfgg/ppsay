import requests
from pymongo import MongoClient
from flask import Flask, url_for, render_template, request

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
  article_docs = articles.find({'possible_candidate_matches':
                                {'$elemMatch': {'id': str(person_id)}}}) \
                         .sort([('page.date_published', -1)])

  person_doc = get_person(person_id)

  person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('person.html',
                         articles=article_docs,
                         person=person_doc)

@app.route('/constituency/<int:constituency_id>')
def constituency(constituency_id):
  article_docs = articles.find({'possible_constituency_matches':
                                {'$elemMatch': {'id': "mapit:{}".format(constituency_id)}}}) \
                         .sort([('page.date_published', -1)])

  area_doc = get_mapit_area(constituency_id)
  #posts_doc = get_person(person_id)

  #person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('constituency.html',
                         articles=article_docs,
                         area=area_doc)

dashboard_queries = [{'query': {},
                      'id': 'num_articles',
                      'name': 'Number of articles',},
                     {'query': {'page': None},
                      'id': 'num_articles_no_page',
                      'name': 'Number of unscraped articles',},
                     {'query': {'page.date_published': None},
                      'id': 'num_articles_no_date',
                      'name': 'Number of articles without a date',},
                     {'query': {'possible_candidate_matches': {'$size': 0}},
                      'id': 'num_articles_no_candidates',
                      'name': 'Number of articles with no candidates',},
                     {'query': {'possible_constituency_matches': {'$size': 0}},
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

