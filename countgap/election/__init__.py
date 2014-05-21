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


class Election:
    def __init__(self, candidates, storage=None):
        self.candidates = candidates
        self.storage = storage or MemoryStorage()
        self._results = None

    def run(self):
        raise NotImplementedError

    def print_results(self):
        raise NotImplementedError


