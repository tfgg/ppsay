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
                                {'$elemMatch': {'id_snip': str(constituency_id)}}}) \
                         .sort([('page.date_published', -1)])

  area_doc = get_mapit_area(constituency_id)
  #posts_doc = get_person(person_id)

  #person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('constituency.html',
                         articles=article_docs,
                         area=area_doc)

dashboard_queries = {'num_articles': {},
                     'num_articles_no_page': {'page': None},
                     'num_articles_no_date': {'page.date_published': None},
                     'num_articles_no_candidates': {'possible_candidate_matches': {'$size': 0}},
                     'num_articles_no_constituencies': {'possible_constituency_matches': {'$size': 0}},
                    }
                        
@app.route('/dashboard')
def dashboard():
    stats = {name: articles.find(query).count() for name, query in dashboard_queries.items()}

    return render_template('dashboard.html',
                           **stats)

@app.route('/dashboard/articles/<query_name>')
def dashboard_articles_query(query_name):
    docs = articles.find(dashboard_queries[query_name])

    return render_template('dashboard_query.html',
                           query_name=query_name,
                           articles=docs)

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)

