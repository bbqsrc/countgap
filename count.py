import sys
import argparse
import countgap

if __name__ == "__main__":
    p = argparse.ArgumentParser()

    p.add_argument('--type', '-t')
    p.add_argument('--db', default="stopgap")
    p.add_argument('slug')
    p.add_argument('election', nargs='?')

    args = p.parse_args()

    elections = []
    if args.election is None:
        elections = countgap.get_elections(args.slug, args.db)
    else:
        elections = [args.election]

    for election_name in elections:
        iterator = countgap.get_election_iterator(args.slug, election_name, args.db)
        cands = countgap.get_election_candidates(args.slug, election_name, args.db)

        election = countgap.SchulzeElection(cands)
        election.run(iterator)
        print("\n== %s ==\n" % election_name)
        election.print_results()

