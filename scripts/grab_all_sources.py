import json
from urlparse import urlparse
from ppsay.tasks import task_get_page

sources_domains_text = open('parse_data/sources_news.dat', 'r')

source_domains = []
for line in sources_domains_text:
  source_domains.append(line.split()[0])

sources = set(json.load(open('parse_data/sources.json')))

for source in sources:
  url_parsed = urlparse(source)

  if url_parsed.netloc in source_domains:
    print source
    task_get_page(source, "Source")

