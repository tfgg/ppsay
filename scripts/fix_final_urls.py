from pymongo import MongoClient

client = MongoClient()

db_articles = client.news.articles
db_web_cache = client.news.web_cache

for doc in db_articles.find():
    if not doc['page']:
        continue

    final_urls = []
    for url in doc['page']['urls']:
        doc_web_cache = db_web_cache.find_one({'url': url})
        final_urls.append(doc_web_cache['url_final'])
    doc['page']['final_urls'] = final_urls

    print final_urls

