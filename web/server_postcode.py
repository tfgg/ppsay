import requests
import re
from flask import Blueprint, jsonify, request, abort, url_for, redirect
from ppsay.data import constituencies_index

app = Blueprint("postcode",
                __name__)

def clean_postcode(postcode):
  return re.sub('[^A-Z0-9]', '', postcode.upper())

@app.route('/postcode', methods=['POST'])
def postcode():
  postcode = request.form.get('postcode', None)

  if not postcode:
    return abort(500, "Specify a postcode")

  postcode = clean_postcode(postcode)

  url = "http://mapit.mysociety.org/postcode/{}".format(postcode[:8])
  resp = requests.get(url)

  # Invalid postcode
  if resp.status_code != 200:
    return abort(500, "Invalid mapit response, {}".format(resp.status_code))

  data = resp.json()

  if 'WMC' in data['shortcuts']:
      constituency_id = data['shortcuts']['WMC']

      return redirect(url_for('ppsay.constituency', constituency_id=constituency_id))
  else:
      return abort(500, "Could not find constituency")
