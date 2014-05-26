from ..election.irv import IRVElection, BallotExhaustionError
from ..util import zero_counter

class STVElection(IRVElection):
    def _eliminate_weakest_candidate(self, counter):
        pass

    def _rank_current_ballots(self):
        c = zero_counter(self.candidates)

        for ballot in self.storage.ballots.values():
            blist = ballot.list
            index = ballot.data['current']

            while blist[index] in self._eliminated:
                index += 1
                if index >= len(blist):
                    raise BallotExhaustionError

            c[blist[index]] += ballot.data.get('value', 1)

        return c

