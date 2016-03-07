import sys

from bson import ObjectId
from pymongo import MongoClient
from test import get_classifier
from vec import vecs 

logistic = get_classifier()

def get_machine(article):
    article_vecs = vecs(article.as_dict(), True)
    
    for vec in article_vecs:
        print vec

    machine = {'candidates': {'confirm': [], 'remove': []}}

    for vec in article_vecs:
        confirm = True if logistic.predict(vec['X'])[0] == 1 else False

        if confirm:
            machine['candidates']['confirm'].append(vec['person_id'])
        else:
            machine['candidates']['remove'].append(vec['person_id'])

        print vec['person_name'], logistic.predict_proba(vec['X'])[0]

    return machine

if __name__ == '__main__':
    client = MongoClient()

    db_articles = client.news.articles

    if len(sys.argv) > 1:
        article_id = ObjectId(sys.argv[1])
        articles = db_articles.find({'_id': article_id})
    else:
        articles = db_articles.find()

    for article in articles:
        if 'possible' not in article:
            continue

        print article['_id']

        article['machine'] = get_machine(article)    
        db_articles.save(article)

