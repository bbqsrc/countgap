import sys
import pymongo

from ..election import Ballot

class MongoIterator:
    def __init__(self, cursor, election):
        self.cursor = cursor
        self.election = election

    def __iter__(self):
        return self

    def __next__(self):
        try:
            n = next(self.cursor)

            x = n['data']['elections'][self.election]
            for k, v in x.copy().items():

                # Check for blank field
                if v == '':
                    v = None

                if v is None:
                    x[k] = v
                    continue

                v = int(v)

                # If your ballot exceeds maxsize, there might be a problem.
                if v > sys.maxsize:
                    raise ValueError("candidate value exceeds maxsize")
                x[k] = v

            return Ballot(n['_id'], x)

        except StopIteration as e:
            self.cursor.rewind()
            raise e

    def __len__(self):
        return self.cursor.count()

def get_elections(slug, db="stopgap"):
    db = pymongo.MongoClient()[db]
    ballot = db.ballots.find_one({"poll": slug, 'data': { "$exists": True }})
    return list(ballot['data']['elections'].keys())

def get_election_iterator(slug, election_name, db="stopgap"):
    db = pymongo.MongoClient()[db]
    return MongoIterator(db.ballots.find({
        "poll": slug, 'data': { "$exists": True }
    }), election_name)

def get_election_candidates(slug, election_name, db="stopgap"):
    db = pymongo.MongoClient()[db]
    ballot = db.ballots.find_one({"poll": slug, 'data': { "$exists": True }})
    return list(ballot['data']['elections'][election_name].keys())

