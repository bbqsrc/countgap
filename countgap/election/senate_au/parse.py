import csv
import string

from collections import defaultdict
from math import log

def _convert_ticket_to_list(ticket):
    o = []
    for i in range(len(ticket)):
        o.append(ticket[i+1])
    return o

def from_group_ticket(chars):
    c = 1
    for n, ch in enumerate(reversed(chars)):
        try:
            i = string.ascii_uppercase.index(ch)
        except ValueError as e:
            raise ValueError("chars must be uppercase ASCII only")
        c += (i + n) * (26 ** n)
    return c

def to_group_ticket(n):
    if n < 1:
        raise ValueError

    chars = []

    n -= 1
    if n == 0:
        return 'A'

    i = -1
    while n:
        i += 1
        mod = (n - i) % 26
        n = n // 26
        chars.append(string.ascii_uppercase[mod])

    return ''.join(reversed(chars))

def read_candidates_file(fn):
    with open(fn) as f:
        f.readline() # Skip pointless header

        reader = csv.DictReader(f)

        for record in reader:
            yield {
                "_id": int(record['CandidateID']),
                "state": record['StateAb'],
                "party": record['PartyNm'],
                "surname": record['Surname'],
                "given_names": record['GivenNm']
            }


def read_gvt_file(fn):
    with open(fn) as f:
        f.readline() # Skip pointless header

        reader = csv.DictReader(f)

        candidates = {}
        composite_record = {} # lookup by id; holds {groupName, candidates: {...}, abv
        ticket_record = None
        ticket_no = None
        group_id = None

        for record in reader:
            if group_id != int(record['OwnerGroupID']):
                if group_id is not None:
                    composite_record['tickets'].append(_convert_ticket_to_list(ticket_record))
                    yield composite_record
                
                ticket_record = None
                ticket_no = None

                composite_record = {
                    '_id': int(record['OwnerGroupID']),
                    'state': record['State'],
                    'group': record['OwnerGroupNm'],
                    'ticket': from_group_ticket(record['OwnerTicket']),
                    'candidates': [],
                    'tickets': []
                }
                group_id = composite_record['_id']
            
            # Check if a candidate
            if record['OwnerTicket'] == record['CandidateTicket']:
                #cand = {
                #    "given_name": record['GivenNm'],
                #    "surname": record['Surname'],
                #    "_id": int(record['CandidateID'])
                #}
                composite_record['candidates'].append(int(record['CandidateID']))
                #composite_record['candidates'].append(cand)
            # Check if a new ticket
            if ticket_no != int(record['TicketNo']):
                if ticket_no is not None:
                    composite_record['tickets'].append(_convert_ticket_to_list(ticket_record))
                ticket_no = int(record['TicketNo'])
                ticket_record = {}
            
            ticket_record[int(record['PreferenceNo'])] = int(record['CandidateID'])

        composite_record['tickets'].append(_convert_ticket_to_list(ticket_record))
        yield composite_record

# We don't use the by group only file because it doesn't include ticket names >_>
def read_first_prefs_by_state_file(fn):
    with open(fn) as f:
        f.readline() # Skip pointless header

        reader = csv.DictReader(f)

        for record in reader:
            if int(record['BallotPosition']) != 0:
                continue
            yield {
                "state": record['StateAb'],
                "ticket": from_group_ticket(record['Ticket']),
                "total": int(record['TotalVotes'])
            }

def read_below_the_line_file(fn):
    with open(fn) as f:
        f.readline() # Skip pointless header

        reader = csv.DictReader(f)

        batch = None
        paper = None
        preferences = []

        for record in reader:
            if int(record["Batch"]) != batch or int(record['Paper']) != paper:
                if batch is not None and paper is not None:
                    yield {
                        "preferences": preferences,
                        "batch": batch,
                        "paper": paper
                    }

                batch = int(record['Batch'])
                paper = int(record['Paper'])
                preferences = []

            pref = record['Preference']
            cand_id = int(record['CandidateId'])

            try:
                preferences.append({"candidate": cand_id, "preference": int(pref)})
            except ValueError as e:
                preferences.append({"candidate": cand_id, "preference": None})
        else:
            yield {
                "preferences": preferences,
                "batch": batch,
                "paper": paper
            }


def test():
    path = "/Users/brendan/git/countgap/data/senate-wa-2014" +\
        "/SenateGroupVotingTicketsDownload-17875.csv"
    for i in read_gvt_file(path):
        print(i)

def test2():
    path = "/Users/brendan/git/countgap/data/senate-wa-2014" +\
        "/SenateFirstPrefsByStateByVoteTypeDownload-17875.csv"
    for i in read_first_prefs_by_state_file(path):
        print(i)

def test3():
    path = "/Users/brendan/git/countgap/data/senate-wa-2014" +\
        "/SenateStateBTLPreferences-17875-WA.csv"
    for i in read_below_the_line_file(path):
        print(i)

'''
from countgap.election.senate_au.mongo import import_election_files
import_election_files(
"/Users/brendan/git/countgap/data/senate-wa-2014" +\
"/SenateCandidatesDownload-17875.csv",
"/Users/brendan/git/countgap/data/senate-wa-2014" +\
"/SenateGroupVotingTicketsDownload-17875.csv",
"/Users/brendan/git/countgap/data/senate-wa-2014" +\
"/SenateFirstPrefsByStateByVoteTypeDownload-17875.csv",
"/Users/brendan/git/countgap/data/senate-wa-2014" +\
"/SenateStateBTLPreferences-17875-WA.csv")
'''
