#!/usr/bin/python2
"""
read splits from gnucash and train network
"""
import re
import sys
import argparse
import os
# own modules
from Network import Network as Network
from GnuCashHelper import GnuCashHelper as GnuCashHelper

def main():
    """main function to start"""
    parser = argparse.ArgumentParser(description="to train neuroal network with existing splits read from gnucash database")
    parser.add_argument("-g", "--gnucash-file", help="path to gnucash File", required=True)
    parser.add_argument("-a", "--account", help="full path to gnucach account to export from, split by dot", required=True)
    parser.add_argument("-i", "--input-file", help="input network state file", required=True)
    options = parser.parse_args()
    if not os.path.isfile(options.gnucash_file):
        print("gnucash file %s does not exist" % options.gnucash_file)
        sys.exit(1)
    # get in contact with gnucash
    gch = GnuCashHelper(options.gnucash_file)
    try:
        # load data from network state file
        network = Network.from_json(open(options.input_file, "rb").read())
        # some tokens, which appear in far to much bookings
        blacklist_tokens = ["telfs", "6410", "k001", "k002", "k003", "k004"]
        # iterate through all bookings of given account
        for entry in gch.gnucash_export(options.account):
            t = gch.tokenizer(entry, blacklist_tokens)
            if t is not None:
                category, tokens = t
                p = network.predict(tokens)
                score, predicted = p
                if category.decode("utf-8") != predicted:
                    print("%(date)s %(num)s %(soll_value)s %(haben)s %(description)20s" % entry)
                    print("\t%s : %s" % (predicted, score))
            else:
                print("%(date)s %(num)s %(soll_value)s %(haben)s %(description)20s" % entry)
    finally:
        gch.end()

if __name__ == "__main__":
    main()
