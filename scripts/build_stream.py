from ppsay.db import db_articles
from ppsay.article import Article

docs = db_articles.find()

for doc in docs:
    if 'pages' not in doc:
        print doc

    article = Article(doc)
    print article.id
    article.update_stream()

