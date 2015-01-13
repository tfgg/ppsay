from iso8601 import parse_date
import re
import sys
import requests
import json
import pytz
import feedparser
from datetime import datetime, timedelta
from pymongo import MongoClient

from ppsay.sources import add_source

client = MongoClient()

db_articles = client.news.articles
db_candidates = client.news.candidates

def save_person(person):
    if person['party_memberships']:
        candidacies = {year: {'party': {'name': x['name'],
                                        'id': x['id'].split(':')[1],},
                              'constituency': {'name': person['standing_in'][year]['name'], 
                                               'id': person['standing_in'][year]['post_id'],}
                             } 
                       for year, x in person['party_memberships'].items() if x is not None}
    else:
        candidacies = {}

    candidate = {'name': person['name'].strip(),
                 'other_names': [x['name'] for x in person['other_names']],
                 'url': person['url'],
                 'id': person['id'],
                 'candidacies': candidacies,}

    candidate_doc = db_candidates.find_one({'id': person['id']})

    if candidate_doc is not None:
        candidate_doc.update(candidate)
    else:
        candidate_doc = candidate

    db_candidates.save(candidate_doc)

sources = []

feed_url = "http://yournextmp.com/feeds/changes.xml"

feed = feedparser.parse(feed_url)

time_now = datetime.now(pytz.utc)

print "Checking at", time_now

person_ids_done = set()

for item in feed['items']:
    person_id = item['id'].split('/')[-1]

    if person_id in person_ids_done:
        print "Skipping", person_id
        continue

    update_time = parse_date(item['summary'].split('Updated at ')[-1])

    if update_time + timedelta(minutes=15) > time_now:
        print "Getting {}".format(person_id)
        url = "http://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(person_id)

        resp = requests.get(url).json()

        person = resp['result']

        save_person(person)

        person_ids_done.add(person_id)

        # Look for any new sources
        for version in person['versions']:
            sources.append(version['information_source'])

print "Processing sources"

url_regex = re.compile("(http|https)://([^\s]+)")

for source in sources:
    matches = url_regex.findall(source)
  
    for match in matches:
        source_url = "{}://{}".format(*match)
        add_source(source_url, 'ynmp-recent')
 
