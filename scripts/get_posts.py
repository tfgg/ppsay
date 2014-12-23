import requests
import json

resp = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/posts?embed=membership.person").json()

constituencies = {}
candidates = {}

while resp:
  print "{} / {}".format(resp['page'], (resp['total'] / resp['per_page'] + 1))

  for post in resp['result']:
    constituencies[post['area']['name']] = post['area']

    for membership in post['memberships']:
      parties = {(x['name'], x['id']) for x in membership['person_id']['party_memberships'].values()}

      candidates[membership['person_id']['id']] = {'name': membership['person_id']['name'],
                    'url': membership['person_id']['url'],
                    'id': membership['person_id']['id'],
                    'parties': [{'name': name, 'id': id} for name, id in parties],}

  json.dump(candidates.values(), open('parse_data/candidates.json', 'w+'), indent=4, sort_keys=True)
  json.dump(constituencies.values(), open('parse_data/constituencies.json', 'w+'), indent=4, sort_keys=True)

  resp = requests.get(resp['next_url'] + "&embed=membership.person").json()

