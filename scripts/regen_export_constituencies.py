import json

from ppsay.article import get_articles
from ppsay.constituency import (
    constituency_get_candidates,
    filter_candidate_or_incumbent,
)
from ppsay.data import (
    constituencies,
    constituencies_index,
    constituencies_names,
    get_candidate,
    get_candidates,
)

export_data = {}

constituency_ids = constituencies_index.keys()

for constituency_id in constituency_ids:
    candidate_docs = constituency_get_candidates(constituency_id)
    person_ids = filter_candidate_or_incumbent(candidate_docs, constituency_id)

    article_docs = get_articles(person_ids, [constituency_id])

    article_docs = sorted(article_docs, key=lambda x: x['order_date'], reverse=True)

    export_data[constituency_id] = [{'url': doc['page']['urls'][0],
                                     'title': doc['page']['title'],
                                     'source': doc.get('domain'),
                                     'date': doc['order_date'].isoformat(),} for doc in article_docs[:10]]

print json.dumps(export_data)

