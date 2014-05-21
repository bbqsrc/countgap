import sys

class MongoIterator:
    def __init__(self, cursor, election):
        self.cursor = cursor
        self.election = election

    def __iter__(self):
        return self

    def __next__(self):
        try:
            n = next(self.cursor)

            x = n['ballot']['elections'][self.election]
            for k, v in x.items():

                # Check for blank field
                if v == '':
                    v = None

                if v is None:
                    x[k] = v
                    continue

                v = int(v)

                # If your ballot exceeds maxsize, there might be a problem.
                if v > sys.maxsize:
                    raise ValueError("candidate value exceeds maxsize")
                x[k] = v

            return Ballot(n['_id'], x)

        except StopIteration as e:
            self.cursor.rewind()
            raise e

    def __len__(self):
        return self.cursor.count()



