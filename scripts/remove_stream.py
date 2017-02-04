from ppsay.db import db_articles
from ppsay.article import Article

docs = db_articles.find()

for doc in docs:
    article = Article(doc)

    print article.id

    num_final_candidates =len([x for x in article.analysis['final']['candidates'] if x['state'] not in ['removed', 'removed_ml']])
    num_final_constituencies =len([x for x in article.analysis['final']['constituencies'] if x['state'] not in ['removed', 'removed_ml']])

    if num_final_candidates == 0 and num_final_constituencies == 0:
        article.update_stream()

