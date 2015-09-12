from ppsay.domains import get_domain, add_domain
from ppsay.db import db_articles

for article in db_articles.find({'state': 'approved'}):
    article_domain = article.get('domain')

    if article_domain is not None:
        domain = get_domain(article_domain)

        if domain is None:
            new_domain = add_domain(article_domain)
            print new_domain

