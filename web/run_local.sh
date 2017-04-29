mkdir -p /tmp/ppsay-test

uwsgi --http-socket 10.132.0.3:8000 --wsgi-file server.py --callable app --chmod-socket=666 --catch-exceptions --max-requests 50 --memory-report --processes 2 --master --pidfile /tmp/ppsay-test/server.pid
