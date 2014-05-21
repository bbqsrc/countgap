from ..util import zero_counter
from ..election import Election

class BallotExhaustionError(ValueError): pass

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

