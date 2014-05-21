from io import StringIO
from string import ascii_uppercase
from collections import defaultdict

from ..util import create_matrix, zero_counter
from ..election import Results, Election

class SchulzeResults(Results):
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

