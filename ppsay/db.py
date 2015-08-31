from pymongo import MongoClient

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles
db_web_cache = db_client.news.web_cache
db_candidates = db_client.news.candidates
db_users = db_client.news.users
db_action_log = db_client.news.action_log
db_domains = db_client.news.domains
db_areas = db_client.news.areas

