from __future__ import division
from ppsay.db import db_events
from collections import Counter, defaultdict
from numpy import mean, median

events = db_events.find({'event': 'article_click'})

sections = Counter()
ips = Counter()
ips_d = defaultdict(list)

for event in events:
    url = event['url']
    val = event['value']
    client_ip = event['client_ip']

    url_bits = url.split('/')[3:]

    sections[url_bits[0]] += 1
    ips[client_ip] += 1
    ips_d[client_ip].append(event)

print "# Clicks per section"
for section, count in sections.items():
    if section == "":
        section = "home"

    print "{} = {}".format(section, count)

print
print "# Clicks per user"
print "max = {}".format(max(ips.values()))
print "min = {}".format(min(ips.values()))
print "mean = {}".format(mean(ips.values()))
print "median = {}".format(median(ips.values()))

#for ip, count in ips.most_common():
#    print "{} = {}".format(ip, count)
all_dts = []
for ip, events in ips_d.items():
    events = sorted(events, key=lambda x: x['time_client'])
    ts = [x['time_client'] for x in events]
    dts = [t1-t0 for t0, t1 in zip(ts[0:-1], ts[1:])]
    
    #print ip, "=", ", ".join(["{}m{}s".format(dt.seconds // 60, dt.seconds % 60) for dt in dts])

    all_dts += dts

all_dts = sorted(all_dts)

print
print "# Time between clicks"
print "all =", ", ".join(["{}m{}s".format(dt.seconds // 60, dt.seconds % 60) for dt in all_dts])
print "mean = {}".format(mean([x.seconds for x in all_dts]))
print "median = {}".format(median([x.seconds for x in all_dts]))

