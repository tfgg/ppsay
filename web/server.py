from bson import ObjectId
from pymongo import MongoClient

import yaml
import smtplib
from flask import Flask
from server_ppsay import app as ppsay_app
from server_postcode import app as postcode_app
from server_users import users as users_app
from flask import (
    Flask,
    request,
    send_from_directory,
    render_template
)
from flask.ext.mail import Mail, Message
import os

config = yaml.load(open('config/general.yaml'))

app = Flask(__name__)
app.register_blueprint(ppsay_app)
app.register_blueprint(postcode_app)
app.register_blueprint(users_app)

app.config.update(
  MAIL_SERVER = config['mail_server'],
  MAIL_PORT = config['mail_port'],
  MAIL_USE_SSL = config['mail_use_ssl'],
  MAIL_USERNAME = config['mail_username'],
  MAIL_PASSWORD = config['mail_password'],
)

mail = Mail(app)

try:
    db_client = MongoClient()
except ConnectionFailure:
    print "Can't connect to MongoDB"
    sys.exit(0)

db_articles = db_client.news.articles

@app.route('/article/<doc_id>/report', methods=['GET', 'POST'])
def article_report(doc_id):
    doc_id = ObjectId(doc_id)

    doc = db_articles.find_one({'_id': doc_id})

    if request.method == 'GET':
        return render_template('abuse_report.html',
                               article=doc)
    elif request.method == 'POST':
        text = request.form.get('text')
        reply_email = request.form.get('email')

        msg = Message('Report on Election Mentions from {}'.format(reply_email),
                      sender=config['mail_sender'],
                      recipients=config['report_emails'])

        msg.body = render_template('abuse_email.txt',
                                   article=doc,
                                   text=text,
                                   reply_email=reply_email)

        error = None
        try:
          mail.send(msg)
        except smtplib.SMTPRecipientsRefused:
          print >>sys.stderr, "Could not send email"
          error = "Could not send email."

        return render_template('abuse_report_sent.html',
                               reply_email=reply_email,
                               text=text,
                               article=doc,
                               error=error)

@app.route('/export.people.quotes.json')
@app.route('/export.people.json')
@app.route('/export.json')
@app.route('/robots.txt')
@app.route('/google894643c5489ee5cd.html')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

app.secret_key = config['secret_key'] 

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)
