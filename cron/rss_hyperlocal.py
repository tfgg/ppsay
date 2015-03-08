import sys
from ppsay.sources import get_source_if_matches
from ppsay.hyperlocal_data import hyperlocal_sites
import feedparser

#skip = True

for site in hyperlocal_sites:
    hyperlocal_site = site['hyperlocal_site']

    party_affiliation = hyperlocal_site['party_affiliation']

    if party_affiliation is not None:
        party_affiliation = party_affiliation.strip()

    feed_url = hyperlocal_site['feed_url']

    #if "www.wansteadium.com" in feed_url:
    #    skip = False
    #    continue
    #elif skip:
    #    continue

    if feed_url:
        print feed_url, party_affiliation

        feed = feedparser.parse(feed_url)

        def clean_link(x):
            return x.split('#')[0]

        for item in feed['items']:
            url = clean_link(item['link'])
            print url
            get_source_if_matches(url,
                                  'rss/hyperlocal',
                                  'approved',
                                  min_candidates=1,
                                  min_parties=1,
                                  min_constituencies=0)

