import math

from ..util import zero_counter
from ..election import Election

class BallotExhaustionError(ValueError): pass

class IRVElection(Election):
    def run(self, ballots, winners=1):
        self._round = 0
        self._eliminated = set()
        self._winners = []
        self._winner_count = winners

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
            print("(%s) %s [%s]" % (c, k, v))
        print()


    @property
    def _quota(self):
        # Droop!
        return math.ceil(math.floor(self._total_ballots / (self._winner_count + 1)) + 1)

    def _rank_current_ballots(self):
        for ballot in self.storage.ballots.values():
            blist = ballot.list
            index = ballot.data['current']

            if index == -1 or blist[index] in self._eliminated:
                while index == -1 or blist[index] in self._eliminated:
                    index += 1
                    if index >= len(blist):
                        raise BallotExhaustionError
                ballot.data['current'] = index
                self._current[blist[index]] += ballot.data.get("value", 1)
                
                print("Transferred %d votes from [%s] to [%s]" % (
                    ballot.data.get("value", 1),
                    ballot.id,
                    blist[index]))

    def _first_count(self, ballots):
        self._total_ballots = 0
        for ballot in ballots:
            v = ballot.data.get('value', 1)
            self._total_ballots += v
            ballot.data['original_value'] = v
            ballot.data['current'] = -1
            self.storage.ballots[ballot.id] = ballot
        
        print("Total ballots: %s" % self._total_ballots)
        print("Quota: %s\n" % self._quota)
        self._rank_current_ballots()

    def _candidate_has_quota(self, counter):
        return counter.most_common()[0][1] >= self._quota

    def _eliminate_weakest_candidate(self, counter):
        # TODO: add proper tie-breaking here, don't rely on __hash__ magic
        bye_bye = counter.most_common()[-1][0]

        print("Eliminated: %s" % bye_bye)

        if bye_bye in self._eliminated:
            raise Exception("This should never happen.")

        self._eliminated.add(bye_bye)
        for gone in self._eliminated:
            del counter[gone]

        return bye_bye

    def _redistribute_values(self, target, total_votes):
        divisor = (total_votes - self._quota) / total_votes

        for ballot in self.storage.ballots.values():
            index = ballot.data['current']
            blist = ballot.list
            if blist[index] == target:
                while blist[index] in self._eliminated:
                    index += 1
                    if index >= len(blist):
                        raise BallotExhaustionError
                ballot.data['current'] = index
                transfer = math.floor(ballot.data['value'] * divisor)
                ballot.data['value'] = transfer
                self._current[blist[index]] += transfer
                
                print("Transferred %d votes from [%s] to [%s] at transfer value [%.4f]" % (
                    transfer,
                    ballot.id,
                    blist[index],
                    divisor))

    def _declare_winner(self, winner):
        print("Elected: %s" % winner)

        self._winners.append(winner)
        self._eliminated.add(winner)
        del self._current[winner]


    def _elect_candidate(self, counter):
        winner = counter.most_common()[0]

        self._declare_winner(winner[0])

        if len(self._winners) >= self._winner_count:
            return

        self._redistribute_values(winner[0], winner[1])


    def _declare_election(self):
        print("\n# Winners:")
        for n, w in enumerate(self._winners):
            print("(%s) %s" % (n+1, w))

    def _next_round(self, ballots):
        if len(self._winners) >= self._winner_count:
            self._declare_election()
            return True

        self._round += 1
        print("\n# Round %s\n" % self._round)

        self._results = self._current
        self.print_results()
        c = self._current

        if len(c) == self._winner_count - len(self._winners):
            print("# Exhausted all ballots!\n")
            for w in c.most_common():
                self._declare_winner(w[0])
            return False

        if self._candidate_has_quota(c):
            self._elect_candidate(c)
        else:
            self._eliminate_weakest_candidate(c)

        self._rank_current_ballots()
        return False
