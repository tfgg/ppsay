import sys
import requests
import json
import re

resp = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/persons").json()


while resp:
  print >>sys.stderr, resp['page']

  for person in resp['result']:
    for version in person['versions']:
      print version['information_source'].encode('utf-8')

  if 'next_url' in resp:
    resp = requests.get(resp['next_url'] + "&embed=membership.person").json()
  else:
    break


