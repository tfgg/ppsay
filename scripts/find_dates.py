import re
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

months = {'January': 1,
          'February': 2,
          'March': 3,
          'April': 4,
          'May': 5,
          'June': 6,
          'July': 7,
          'August': 8,
          'September': 9,
          'October': 10,
          'November': 11,
          'December': 12,}

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
  
        # Fri 24th October 2014 - 8:49 am 
        # Lib dem voice
        for div in tree.xpath('//div[@class="entry-meta"]'):
            text = div.text_content().split('|')[-1].strip()
            cols = re.findall("([A-Za-z]+) ([0-9]+)(st|nd|rd|th) ([A-Za-z]+) ([0-9]+) - ([0-9]+):([0-9]+) (am|pm)", text)

            if len(cols) > 0:
                cols = cols[0]
                year = int(cols[4])
                month = months[cols[3]]
                day = int(cols[1])
                hours = int(cols[5])
                minutes = int(cols[6])
                if cols[7] == 'pm':
                    hours += 12

                parsed_time = datetime(year, month, day, hours, minutes)
                dates.append(parsed_time)
            else:
                s = """Isle of Wight News"""
                text = text[len(s):].strip()
                parsed_time = datetime.strptime(text, "%B %d, %Y")
                dates.append(parsed_time)

    if dates:
        earliest_date = min(dates)

        doc['page']['date_published'] = earliest_date

        db_articles.save(doc)

#print names

