#!/usr/bin/python2
"""
read splits from gnucash and train network
"""
import re
import sys
import argparse
import os
import json
# own modules
from Categorizer import Categorizer as Categorizer
from Network import Network as Network
from GnuCashHelper import GnuCashHelper as GnuCashHelper

def gc_export(account):
    """
    read gnucash generated export file of aufwaendungen
    """
    blacklist_tokens = ["telfs", "6410", "k001", "k002", "k003", "k004"]
    for entry in gch.gnucash_export(account):
        yield gch.tokenizer(entry, blacklist_tokens)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="to train neuroal network with existing splits read from gnucash database")
    parser.add_argument("-g", "--gnucash-file", help="path to gnucash File", required=True)
    parser.add_argument("-a", "--account", help="full path to gnucach account to export from, split by dot", required=True)
    parser.add_argument("-o", "--output", help="output neural network state to this file", required=True)
    options = parser.parse_args()
    if not os.path.isfile(options.gnucash_file):
        print("gnucash file %s does not exist" % options.gnucash_file)
        sys.exit(1)
    # get in contact with gnucash
    gch = GnuCashHelper(options.gnucash_file)
    try:
        latest_booking = gch.get_latest_booking(options.account)
        # start with empty brain
        network = Network()
        # this step is necessary to get all possible tokens for every category
        for category, tokens in gc_export(options.account):
            network.read(category, tokens)
        # train network, to adjust values for tokens
        for category, tokens in gc_export(options.account):
            network.train(category, tokens)
        # cleanup data, and remove tokens who are below threshold
        network.remember()
        # at this point network is trained with initial data
        print("saving actual state of network")
        open(options.output, "wb").write(network.to_json())
        print("analyzed bookings until %s %s" % (latest_booking["date"], latest_booking["num"]))
    finally:
        gch.end()
