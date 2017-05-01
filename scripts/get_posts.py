from __future__ import print_function

import json
import requests

url = "https://candidates.democracyclub.org.uk/api/v0.9/posts/?format=json"

records = []

while True:
  print(url)
  response = requests.get(url)
  response_json = response.json()

  for result in response_json["results"]:
    records.append(result)

  url = response_json["next"]
  if url is None:
    break

print("Found {} posts".format(len(records)))

json.dump({"results": records}, open("posts.json", "w+"))
