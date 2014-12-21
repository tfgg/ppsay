import requests
import json
import re

resp = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/persons").json()

sources = []

url_regex = re.compile("(http|https)://([^\s]+)")

while resp:
  for person in resp['result']:
    for version in person['versions']:
      matches = url_regex.findall(version['information_source'])

      for match in matches:
        url = "{}://{}".format(*match)
        sources.append(url)

  with open('parse_data/sources.json', 'w+') as f:
    json.dump(sources, f)

  if 'next_url' in resp:
    resp = requests.get(resp['next_url'] + "&embed=membership.person").json()
  else:
    break

print "FINISHED"

