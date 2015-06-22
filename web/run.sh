mkdir -p /tmp/ppsay

uwsgi --socket /tmp/ppsay/server.sock --wsgi-file server.py --callable app --chmod-socket=666 --daemonize /tmp/ppsay/server-web-ppsay.log --catch-exceptions --max-requests 50 --memory-report --processes 2 --master --pidfile /tmp/ppsay/server.pid
