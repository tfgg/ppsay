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
      candidacies = {year: {'party': {'name': x['name'],
                                      'id': x['id'].split(':')[1],},
                            'constituency': {'name': membership['person_id']['standing_in'][year]['name'], 
                                             'id': membership['person_id']['standing_in'][year]['post_id'],}
                           } 
                     for year, x in membership['person_id']['party_memberships'].items() if x is not None}

      candidates[membership['person_id']['id']] = {'name': membership['person_id']['name'].strip(),
                    'other_names': [x['name'] for x in membership['person_id']['other_names']],
                    'url': membership['person_id']['url'],
                    'id': membership['person_id']['id'],
                    'candidacies': candidacies,}

  json.dump(candidates.values(), open('parse_data/candidates.json', 'w+'), indent=4, sort_keys=True)
  json.dump(constituencies.values(), open('parse_data/constituencies.json', 'w+'), indent=4, sort_keys=True)

  resp = requests.get(resp['next_url'] + "&embed=membership.person").json()

