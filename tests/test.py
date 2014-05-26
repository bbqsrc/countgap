import sys
sys.path.insert(0, '..')
import countgap
import pymongo

def test():
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

def test2():
    from countgap.election.senate_au.mongo import federal_ballots_iterator
    
    candidates = ["%s %s [%s]" % (x['given_names'], x['surname'], x['party']) for x in 
                    pymongo.Connection().federalElections.candidates.find({"state": "WA"})]


    iterator = federal_ballots_iterator('WA')

    election = countgap.IRVElection(candidates)
    election.run(iterator, winners=6)
    #election.print_results()

if __name__ == "__main__":
    test2()

