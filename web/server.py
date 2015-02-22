from flask import Flask
from server_ppsay import app as ppsay_app
from flask import Flask, request, send_from_directory

#url_prefix = "/articles"

app = Flask(__name__)
app.register_blueprint(ppsay_app)#, url_prefix=url_prefix)

@app.route('/robots.txt')
@app.route('/google894643c5489ee5cd.html')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
  app.run("0.0.0.0", debug=True)
