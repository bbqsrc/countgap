import sys
sys.path.insert(0, '..')
import countgap

if __name__ == "__main__":
    import pymongo
    db = pymongo.Connection().stopgap
    election_db = db.elections.find_one({"slug": "piratecon2013"})

    db_ballot = db.ballots.find_one({
        "election_id": election_db['_id']})
    candidates = list(db_ballot['ballot']['elections']['Councillor'].keys())

    iterator = countgap.MongoIterator(db.ballots.find({
        "election_id": election_db["_id"]}), "Councillor")

    election = countgap.SchulzeElection(candidates)
    election.run(iterator)
    election.print_results()
