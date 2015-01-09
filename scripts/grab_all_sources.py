import json
from urlparse import urlparse
from ppsay.tasks import task_get_page
from ppsay.domains import domain_whitelist

sources = set(json.load(open('parse_data/sources.json')))

for source in sources:
  url_parsed = urlparse(source)

  if url_parsed.netloc in domain_whitelist:
    print source
    task_get_page(source, "Source")

