from .parse import *
from countgap.election import Ballot

import pymongo
from bson.dbref import DBRef

class ValuedBallot(Ballot):
    def __init__(self, id, ballots, value):
        super().__init__(id, ballots)
        self._value = value

    @property
    def value(self):
        return self._value


def import_election_files(candidates, gvt, first_prefs, btl):
    db = pymongo.Connection().federalElections
    
    for record in read_candidates_file(candidates):
        db.candidates.insert(record)

    for record in read_gvt_file(gvt):
        for i in range(len(record['candidates'])):
            record['candidates'][i] = DBRef('candidates', record['candidates'][i])
        db.gvt.insert(record)

    for record in read_first_prefs_by_state_file(first_prefs):
        db.firstPrefs.insert(record)
    
    for record in read_below_the_line_file(btl):
        for pref in record['preferences']:
            pref['candidate'] = DBRef('candidates', pref['candidate'])
        db.belowTheLine.insert(record)

def get_candidates():
    db = pymongo.Connection().federalElections

    

def _split_number(total, amt):
    base = total // amt
    mod = total % amt
    o = []
    for _ in range(amt):
        x = base
        if (mod > 0):
            x +=  1
            mod -= 1
        o.append(x)
    return tuple(o)


def federal_ballots_iterator(state):
    db = pymongo.Connection().federalElections

    candidates = {}
    for x in db.candidates.find():
        candidates[x['_id']] = "%s %s [%s]" % (x['given_names'], x['surname'], x['party'])

    # Yield the above the lines
    i = 0
    for record in db.gvt.find({"state": state}):
        i += 1
        votes = db.firstPrefs.find_one({"state": state, "ticket": record['ticket']})['total']
        split_votes = _split_number(votes, len(record['tickets']))
        
        for n, ticket in enumerate(record['tickets']):
            for j in range(len(ticket)):
                ticket[j] = candidates[ticket[j]]
            ballot = Ballot("%s (Ticket %s)" % (record['group'], n+1), ticket)
            ballot.data['value'] = split_votes[n]
            yield ballot

    # Yield the below the lines, if even possible
