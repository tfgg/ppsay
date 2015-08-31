from ppsay.data import constituencies, constituencies_names
from ppsay.db import db_areas

for constituency in constituencies:
    old_doc = db_areas.find_one({'id': constituency['id']})

    doc = {
        'id': constituency['id'],
        'name': constituency['name'],
        'other_names': list(set(constituencies_names[constituency['id']]) - {constituency['name']}),
        'links': {
            'mapit': {
                'url': constituency['identifier'],
                'identifier': constituency['id'],
            },
         },
    }

    if old_doc is None:
        db_areas.save(doc)
    else:
        old_doc.update(doc)
        db_areas.save(old_doc)
            
