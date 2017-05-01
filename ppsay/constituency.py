from ppsay.db import db_candidates
from ppsay.data import elections

def constituency_get_candidates(constituency_id):
    """Fetches all the (non-deleted) candidates in a given constituency.

    Args:
      constituency_id: string, a constituency identifier.

    Returns:
      A list of candidate data dictionaries.
    """
    candidate_docs = {}

    for election_id in elections:
        query = {
            "deleted": False,
            "candidacies.{}.constituency.id".format(election_id): constituency_id,
        }

        for candidate in db_candidates.find(query):
            candidate_docs[candidate["id"]] = candidate

    candidate_docs = sorted(candidate_docs.values(), key=lambda x: x["name"])

    return candidate_docs

def filter_candidate_or_incumbent(candidate_docs, constituency_id):
    person_ids = [x["id"] for x in candidate_docs]
    
    return person_ids


