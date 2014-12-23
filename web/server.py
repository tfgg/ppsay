import requests
from pymongo import MongoClient
from flask import Flask, url_for, render_template, request

db_client = MongoClient()

articles = db_client.news.articles

app = Flask(__name__)

def get_person(person_id):
  req = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(person_id))

  return req.json()['result']

@app.route('/')
def index():
  article_docs = articles.find()

  return render_template('index.html',
                         articles=article_docs)

@app.route('/person/<person_id>')
def person(person_id):
  article_docs = articles.find({'possible_candidate_matches':
                                  {'$elemMatch': {'id': person_id}}})

  person_doc = get_person(person_id)

  person_doc['current_party'] = person_doc['party_memberships'][max(person_doc['party_memberships'])]

  return render_template('person.html',
                         articles=article_docs,
                         person=person_doc)

if __name__ == "__main__":
  app.run(debug=True)
