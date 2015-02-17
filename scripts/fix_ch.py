from pymongo import MongoClient
from ppsay.article import ArticleGeneric

client = MongoClient()

db = client.news.web_cache
articles = client.news.articles

docs = db.find()

for doc in docs:
    if 'http://www.conservativehome.com' in doc['url']:
        print doc['_id'], doc['url']
        if not doc.get('ch_fix', False):
            try:
                new_html = doc['html'].encode('latin_1').decode('utf-8')
                doc['html'] = new_html
                doc['ch_fix'] = True
                db.save(doc)
            except Exception, e:
                print e

        # update articles that use this one
        article_doc = articles.find_one({'key': doc['url']})

        if article_doc:
            print article_doc['_id']
            article = ArticleGeneric(doc['url'])
            article_doc['page'] = article.as_dict()
            articles.save(article_doc)

