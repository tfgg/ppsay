from pymongo import MongoClient
import lxml.html
from iso8601 import parse_date
from datetime import datetime

client = MongoClient()

db_articles = client.news.articles
db_web_cache = client.news.web_cache

docs = db_articles.find()

time_names = {'DC.date.issued': lambda s: datetime(*map(int, s.split('-'))), 
              'DCTERMS.created': parse_date,
              'OriginalPublicationDate': lambda s: parse_date(s.replace('/', '-')),
              'DCTERMS.modified': parse_date,
              'published-date': lambda s: datetime.strptime(s, "%a, %d %b %Y %H:%M:%S GMT"), # Sat, 22 Nov 2014 11:15:00 GMT
              'pubdate': lambda s: datetime(int(s[0:4]), int(s[4:6]), int(s[6:8])),
             }



#names = set()

for doc in docs:
    if not doc['page']:
        continue

    url = doc['page']['url']
    web_cache_doc = db_web_cache.find_one({'url': url})
    
    dates = []

    if web_cache_doc['html']:
        tree = lxml.html.fromstring(web_cache_doc['html'])
        for meta in tree.xpath('//meta'):
            if 'name' in meta.attrib and meta.attrib['name'] in time_names:
                parsed_time = time_names[meta.attrib['name']](meta.attrib['content'])

                dates.append(parsed_time)


        # Particular newspaper CMS with lots of domains
        for div in tree.xpath('//div[@class="updated  Published"]/p'):
            parsed_time = datetime.strptime(div.text, 'Published %d/%m/%Y %H:%M')
            dates.append(parsed_time)
   
        # Lib dem voice
        for div in tree.xpath('//div[@class="entry-meta"]'):
            print div.text_content().split('|')[-1].strip()
 
    if dates:
        earliest_date = min(dates)

        doc['page']['date_published'] = earliest_date

        db_articles.save(doc)

#print names

