from flask import Flask
from server_ppsay import app as ppsay_app
from server_postcode import app as postcode_app
from server_users import users as users_app
from flask import Flask, request, send_from_directory
import os
#url_prefix = "/articles"

app = Flask(__name__)
app.register_blueprint(ppsay_app)#, url_prefix=url_prefix)
app.register_blueprint(postcode_app)
app.register_blueprint(users_app)

@app.route('/robots.txt')
@app.route('/google894643c5489ee5cd.html')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

app.secret_key = os.urandom(8) 

if __name__ == "__main__":
  app.secret_key = 'DEBUGGING-LALALA'
  app.run("0.0.0.0", debug=True)
