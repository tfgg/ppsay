from collections import defaultdict

from ppsay import db
from ppsay import data


def make_election_id(election_id):
  """Normalizes election ID for internal use.

  Periods must be removed in order to use them as keys in MongoDB.

  Args:
    election_id: string, election ID as given by Candidates.

  Returns:
    Election ID for internal use.
  """

  if election_id == "2010" or election_id == "ge2010":
    return "parl_2010-05-06"
  elif election_id == "2015" or election_id == "ge2015":
    return "parl_2015-05-07"
  else:
    return election_id.replace(".", "_")


def transform_person(person):
    """Transforms a Candidates person result into the internal format.

    Args:
      person: dict, person record returned by Candidates API.

    Returns:
      A dictionary, representing internal candidate object.
    """

    if "party_memberships" not in person["versions"][0]["data"]:
        return

    # Make identifiers available as a dictionary. We must remove periods in keys for MongoDB.
    ids = {
        ident["scheme"].replace(".", "_"): ident["identifier"] for ident in person["identifiers"]
    }

    # Not entirely true, might have been in parliament previously but been turfed out?
    incumbent = "uk.org.publicwhip" in ids

    candidacies = {}
    for membership in person["memberships"]:
        party_id = membership["on_behalf_of"]["id"]
        party_name = membership["on_behalf_of"]["name"]

        post = data.posts[membership["post"]["id"]]
        area_id = post["area"]["identifier"]
        area_name = post["area"]["name"]

        election_id = make_election_id(membership["election"]["id"])

        candidacies[election_id] = {
            "party": {
                "id": party_id,
                "name": party_name,
            },
            "constituency": {
                "id": area_id,
                "name": area_name,
            },
           "election_id": election_id.replace("_", "."),
        }

    links = defaultdict(list)

    if person.get("email"):
        links["email"].append({"note": "E-mail", "link": person["email"]})
    
    if person.get("party_ppc_page_url"):
        links["website"].append({"note": "Party PPC page", "link": person["party_ppc_page_url"]})
    
    if person.get("facebook_personal_url"):
        links["facebook_profile"].append({"note": "Personal Facebook profile", "link": person["facebook_personal_url"]})
    
    if person.get("facebook_page_url"):
        links["facebook_page"].append({"note": "Campaign Facebook page", "link": person["facebook_page_url"]})

    if person.get("homepage_url"):
        links["website"].append({"note": "Homepage", "link": person["homepage_url"]})

    if person.get("wikipedia_url"):
        links["wikipedia_url"].append({"note": "Wikipedia page", "link": person["wikipedia_url"]})

    image = None
    if len(person["images"]) > 0:
        image = "https://candidates.democracyclub.org.uk" + person["images"][0]["image_url"]

    candidate = {
        "name": person["name"].strip(),
        "name_prefix": person.get("honorific_prefix", None),
        "name_suffix": person.get("honorific_suffix", None),
        "other_names": [x["name"] for x in person.get("other_names", [])],
        "url": person["url"],
        "id": str(person["id"]),
        "identifiers": ids,
        "links": links,
        "image": image,
        "candidacies": candidacies,
        "gender": person["gender"],
        "incumbent": incumbent,
        "deleted": False,
    }

    return candidate


def save_person(person):
    candidate = transform_person(person)

    if candidate:
        candidate_doc = db.db_candidates.find_one({"id": candidate["id"]})

        if candidate_doc is not None:
            candidate_doc.update(candidate)
        else:
            candidate_doc = candidate

        print candidate_doc["id"]
        db.db_candidates.save(candidate_doc)

        return candidate_doc

    else:
        return

