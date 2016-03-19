from collections import defaultdict

from ppsay.db import db_candidates

def transform_person(person):
    """
        Transform a popit person result into the internal format.
    """

    if 'party_memberships' not in person['versions'][0]['data']:
        return

    ids = {
        ident['scheme'].replace('.', '_'): ident['identifier'] for ident in person['identifiers']
    }

    # Not entirely true, might have been in parliament previously but been turfed out?
    incumbent = 'uk.org.publicwhip' in ids

    def election_id(x):
        if x == '2010':
            return 'parl_2010-05-06'
        elif x == '2015':
            return 'parl_2015-05-07'
        else:
            return x.replace('.', '_')

    data = person['versions'][0]['data']

    if data['party_memberships']:
        candidacies = {
            election_id(elect): {
                'party': {
                    'name': data['party_memberships'][elect]['name'],
                    'id': data['party_memberships'][elect]['id'].split(':')[1],
                },
                'constituency': {
                    'name': data['standing_in'][elect]['name'], 
                    'id': data['standing_in'][elect]['post_id'],
                },
                'election_id': election_id(elect).replace('_', '.'),
            } 
            for elect in data['party_memberships']
            if data['party_memberships'][elect] is not None
               and data['standing_in'][elect] is not None
        }
    else:
        candidacies = {}

    links = defaultdict(list)

    if data.get('email'):
        links['email'].append({'note': 'E-mail', 'link': data['email']})
    
    if data.get('party_ppc_page_url'):
        links['website'].append({'note': 'Party PPC page', 'link': data['party_ppc_page_url']})
    
    if data.get('facebook_personal_url'):
        links['facebook_profile'].append({'note': 'Personal Facebook profile', 'link': data['facebook_personal_url']})
    
    if data.get('facebook_page_url'):
        links['facebook_page'].append({'note': 'Campaign Facebook page', 'link': data['facebook_page_url']})

    if data.get('homepage_url'):
        links['website'].append({'note': 'Homepage', 'link': data['homepage_url']})

    if data.get('wikipedia_url'):
        links['wikipedia_url'].append({'note': 'Wikipedia page', 'link': data['wikipedia_url']})

    image = None
    if len(person['images']) > 0:
        image = "https://candidates.democracyclub.org.uk" + person['images'][0]['image_url']

    candidate = {
        'name': person['name'].strip(),
        'name_prefix': person.get('honorific_prefix', None),
        'name_suffix': person.get('honorific_suffix', None),
        'other_names': [x['name'] for x in person.get('other_names', [])],
        'url': person['url'],
        'id': str(person['id']),
        'identifiers': ids,
        'links': links,
        'image': image,
        'candidacies': candidacies,
        'gender': person['gender'],
        'incumbent': incumbent,
    }

    return candidate


def save_person(person):

    candidate = {
        'name': person['name'].strip(),
        'name_prefix': person.get('honorific_prefix', None),
        'name_suffix': person.get('honorific_suffix', None),
        'other_names': [x['name'] for x in person.get('other_names', [])],
        'url': person['url'],
        'id': str(person['id']),
        'identifiers': ids,
        'image': person.get('image', None),
        'proxy_image': person.get('proxy_image', None),
        'candidacies': candidacies,
        'gender': person['gender'],
        'incumbent': incumbent,
    }

    return candidate


def save_person(person):
    candidate = transform_person(person)

    if candidate:
        candidate_doc = db_candidates.find_one({'id': candidate['id']})

        if candidate_doc is not None:
            candidate_doc.update(candidate)
        else:
            candidate_doc = candidate

        print candidate_doc['id']
        db_candidates.save(candidate_doc)

        return candidate_doc

    else:
        return

