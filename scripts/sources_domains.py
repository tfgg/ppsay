import json
from urlparse import urlparse
from collections import Counter

sources = json.load(open('parse_data/sources.json'))

domains = Counter()

for source in sources:
  parsed_url = urlparse(source)

  domains[parsed_url.netloc] += 1

for domain, count in domains.items():
  print domain, count
