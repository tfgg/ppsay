from ppsay.db import db_candidates

def transform_person(person):
    """
        Transform a popit person result into the internal format.
    """

    if 'party_memberships' not in person:
        print person
        return

    id_schemes = {
        ident['scheme'] for ident in person['identifiers']
    }

    # Not entirely true, might have been in parliament previously but been turfed out?
    incumbent = 'uk.org.publicwhip' in id_schemes

    if person['party_memberships']:
        candidacies = {
            "ge{}".format(year): {
                'party': {
                    'name': person['party_memberships'][year]['name'],
                    'id': person['party_memberships'][year]['id'].split(':')[1],
                },
                'constituency': {
                    'name': person['standing_in'][year]['name'], 
                    'id': person['standing_in'][year]['post_id'],
                },
                'year': year,
            } 
            for year in person['party_memberships']
            if person['party_memberships'][year] is not None
               and person['standing_in'][year] is not None
        }
    else:
        candidacies = {}

    candidate = {
        'name': person['name'].strip(),
        'name_prefix': person.get('honorific_prefix', None),
        'name_suffix': person.get('honorific_suffix', None),
        'other_names': [x['name'] for x in person['other_names']],
        'url': person['url'],
        'id': person['id'],
        'image': person.get('image', None),
        'proxy_image': person.get('proxy_image', None),
        'candidacies': candidacies,
        'gender': person['gender'],
        'incumbent': incumbent,
    }

    return candidate

def save_person(person):
    candidate = transform_person(person)

    candidate_doc = db_candidates.find_one({'id': person['id']})

    if candidate_doc is not None:
        candidate_doc.update(candidate)
    else:
        candidate_doc = candidate

    db_candidates.save(candidate_doc)

