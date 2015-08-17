from iso8601 import parse_date
import re
import sys
import requests
import json
import pytz
import feedparser
from datetime import datetime, timedelta
from pymongo import MongoClient

from ppsay.sources import get_source_whitelist
from ppsay.importers import ynmp

client = MongoClient()

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

        ynmp.save_person(person)

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
        get_source_whitelist(source_url, 'ynmp-recent')
 
