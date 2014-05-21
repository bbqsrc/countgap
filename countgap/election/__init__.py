import logging
import math

from collections import defaultdict, Counter, namedtuple
from io import StringIO
from string import ascii_uppercase

from ..util import create_matrix, zero_counter

class BallotExhaustionError(ValueError): pass

class Ballot:
    def __init__(self, id, ballot_data):
        self.id = id
        self.data = {}

        if isinstance(ballot_data, dict):
            self._ballot_dict = ballot_data
        elif isinstance(ballot_data, list):
            self._ballot_list = ballot_data
        else:
            raise ValueError

    @property
    def list(self):
        if not hasattr(self, '_ballot_list'):
            x = [[] for i in range(len(self._ballot_dict) + 10)]
            for k, v in self._ballot_dict.items():
                x[v-1].append(k)

            self._ballot_list = x
        return self._ballot_list

    @property
    def dict(self):
        if not hasattr(self, '_ballot_dict'):
            x = {}
            for n, k in enumerate(self._ballot_list):
                x[k] = n+1
            self._ballot_dict = x
        return self._ballot_dict


# The idea here is that one could use another backend such as mongo
# to allow resumable counting.
class MemoryStorage:
    @property
    def ballots(self):
        if not hasattr(self, '_ballots'):
            self._ballots = {}
        return self._ballots


class Results:
    @property
    def html(self):
        """Results as HTML"""
        pass

    @property
    def plaintext(self):
        """Results as plain text"""
        pass

class SchulzeResults:
    def __init__(self, score, strongest, rankings, winners=1):
        self._score = score
        self._strongest = strongest
        self._rankings = rankings
        self._winners = winners

    @property
    def plaintext(self):
        return "%s\n\n%s" % (self.rankings_plaintext, self.matrix_plaintext)

    @property
    def rankings_plaintext(self):
        out = "# Rankings:\n\n"
        c = 0
        for k, v in self._rankings.most_common():
            c += 1
            out += "(%s) %s %s\n" % (c, k, "[WINNER]" if c <= self._winners else "")
        return out.strip()

    @property
    def matrix_plaintext(self):
        # Let's try to print this in winner order for once.
        out = StringIO()
        cands = [x[0] for x in self._rankings.most_common()]

        out.write("# Path Matrix:\n\n")
        
        out.write("\n".join(["(%s) %s" % (ascii_uppercase[n], x) for n, x in enumerate(cands)]))
        out.write("\n\n")

        out.write(create_matrix(cands, self._score).getvalue())

        return out.getvalue().strip()


class Election:
    def __init__(self, candidates, storage=None):
        self.candidates = candidates
        self.storage = storage or MemoryStorage()
        self._results = None

    def run(self):
        raise NotImplementedError

    def print_results(self):
        raise NotImplementedError


class IRVElection(Election):
    def run(self, ballots, winners=1):
        self._round = 0
        self._eliminated = set()
        self._total_ballots = len(ballots)
        self._winners = winners

        print("Total ballots: %s" % self._total_ballots)
        print("Quota: %s" % self._quota)

        self._current = zero_counter(self.candidates)
        self._first_count(ballots)

        complete = False
        while not complete:
            complete = self._next_round(ballots)

    def print_results(self):
        if self._results is None:
            raise ValueError

        c = 0
        print("Rankings:")
        for k, v in self._results.most_common():
            c += 1
            if k in self._eliminated:
                continue
            print("(%s) %s [%s]" % (c, k, v))


    @property
    def _quota(self):
        # Droop!
        return math.ceil(math.floor(self._total_ballots / (self._winners + 1)) + 1)

    def _rank_current_ballots(self):
        for ballot in self.storage.ballots.values():
            blist = ballot.list
            index = ballot.data['current']

            if index == -1 or blist[index][0] in self._eliminated:
                while index == -1 or blist[index][0] in self._eliminated:
                    index += 1
                    if index >= len(blist):
                        raise BallotExhaustionError
                ballot.data['current'] = index
                self._current[blist[index][0]] += 1

    def _first_count(self, ballots):
        for ballot in ballots:
            ballot.data['current'] = -1
            self.storage.ballots[ballot.id] = ballot

    def _candidate_has_quota(self, counter):
        # Check that all winners fulfil quota
        common = counter.most_common()
        for i in range(self._winners):
            if common[i][1] < self._quota:
                return False

        return True

    def _eliminate_weakest_candidate(self, counter):
        # TODO: add proper tie-breaking here, don't rely on __hash__ magic
        for gone in self._eliminated:
            del counter[gone]

        bye_bye = counter.most_common()[-1][0]

        print("Eliminated: %s" % bye_bye)

        if bye_bye in self._eliminated:
            raise Exception("This should never happen.")

        self._eliminated.add(bye_bye)
        return bye_bye

    def _elect_candidate(self, counter):
        # winner found!
        print("Winrar.")
        self._results = counter
        self.print_results()
        return True

    def _next_round(self, ballots):
        self._round += 1
        print("\nRound: %s\n" % self._round)

        # check for candidate with 50% + 1 ballots
        self._rank_current_ballots()
        c = self._current

        if self._candidate_has_quota(c):
            return self._elect_candidate(c)

        self._results = c
        self.print_results()
        self._eliminate_weakest_candidate(c)
        return False


class STVElection(IRVElection):
    def _eliminate_weakest_candidate(self, counter):
        pass

    def _rank_current_ballots(self):
        c = zero_counter(self.candidates)

        for ballot in self.storage.ballots.values():
            blist = ballot.list
            index = ballot.data['current']

            while blist[index][0] in self._eliminated:
                index += 1
                if index >= len(blist):
                    raise BallotExhaustionError

            c[blist[index][0]] += 1

        return c

class SchulzeElection(Election):
    def run(self, ballots, winners=1):
        s = self._score_ballots(ballots)
        p = self._calculate_strongest_paths(s)
        r = self._determine_rankings(p)

        if list(r.values()).count(max(r.values())) > 1:
            r = self._break_ties(s, r)

        self._results = SchulzeResults(s, p, r, winners)

    def print_results(self):
        if self._results is None:
            raise ValueError
        
        print(self._results.plaintext)

    def _calculate_strongest_paths(self, score):
        paths = defaultdict(lambda: zero_counter(self.candidates))

        for i in self.candidates:
            for j in self.candidates:
                if i == j: continue
                if score[i][j] > score[j][i]:
                    paths[i][j] = score[i][j]

        for i in self.candidates:
            for j in self.candidates:
                if i == j: continue
                for k in self.candidates:
                    if i != k and j != k:
                        paths[j][k] = max(paths[j][k], min(paths[j][i], paths[i][k]))

        return paths

    def _score_ballots(self, ballots):
        s = defaultdict(lambda: zero_counter(self.candidates))

        for o in ballots:
            ballot = o.dict
            for a in self.candidates:
                for b in self.candidates:
                    # Skip same candidate
                    if a == b:
                        continue

                    # Both equal, neither are lt, thus fail
                    elif ballot[a] == ballot[b]:
                        continue

                    # Both blank, neither are lt, thus fail
                    elif ballot[a] is ballot[b] is None:
                        continue

                    # If a is blank, fail
                    elif ballot[a] is None:
                        continue

                    # all ints < blank or x < y
                    elif ballot[b] is None or ballot[a] < ballot[b]:
                        s[a][b] += 1

        return s

    def _determine_rankings(self, paths):
        ranking = zero_counter(self.candidates)
        for i in paths:
            for j in paths:
                if i == j: continue
                if paths[i][j] > paths[j][i]:
                    ranking[i] += 1

        return ranking


    def _break_ties(self, paths, ranking):
        scores = zero_counter(self.candidates)
        for i in paths:
            if ranking[i] == 0:
                continue
            for j in paths:
                if i == j: continue
                if paths[i][j] > paths[j][i]:
                    scores[i] += paths[i][j] - paths[j][i]

        return scores

