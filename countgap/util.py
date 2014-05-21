from io import StringIO
from string import ascii_uppercase

def create_matrix(keys, values):
    if len(keys) > 26:
        raise ValueError("Not enough alphabet. Write better util code!")

    out = StringIO()
    cols = {}

    # Find widest number first
    for n, j in enumerate(keys):
        cols[j] = 1
        for k in keys:
            if k == j:
                continue
            l = len(str(values[k][j]))
            if l > cols[j]:
                cols[j] = l

    # CREATE HEADER!
    row_sep = "+---+%s+\n" % "+".join(["-" * (cols[k] + 2) for k in keys])
    out.write(row_sep)
    out.write("|   |%s|\n" % "|".join([
        " %s%s " % (
            ascii_uppercase[n], " " * (cols[k] - 1)
        ) for n, k in enumerate(keys)
    ]))
    out.write(row_sep)

    for n, j in enumerate(keys): #y
        v = []
        for k in keys: #x
            if k == j:
                v.append("X")
            else:
                v.append(values[j][k])

        out.write("| %s |%s|\n" % (ascii_uppercase[n], ("|".join([
            " %s%s " % (
                v[n], " " * (cols[z] - len(str(v[n])))
            ) for n, z in enumerate(keys)
        ]))))

        out.write(row_sep)

    return out

def test():
    return create_matrix(['a', 'b', 'c'], {
        'a': {'b': 2, 'c': 3},
        'b': {'a': 1, 'c': 3},
        'c': {'a': 1, 'b': 2}
    })

