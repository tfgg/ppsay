from flask import Flask
from server_ppsay import app as ppsay_app

url_prefix = "/articles"

app = Flask(__name__)
app.register_blueprint(ppsay_app, url_prefix=url_prefix)

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)
