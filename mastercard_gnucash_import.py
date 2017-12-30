#!/usr/bin/python2
# -*- coding: utf-8 -*-
import os
import sys
import codecs
import re
import glob
import datetime
import argparse
import logging
logging.basicConfig(level=logging.DEBUG)
# own modules
from Network import Network as Network
from GnuCashHelper import GnuCashHelper as GnuCashHelper

def bawag_mc_export_reader():
    """
    read bawag specific export file and return dict
    """
    buchungen = {}
    for filename in glob.glob(os.path.join(options.export_dir, "PSK_Umsatzliste_*_kreditkarte.csv")):
        with codecs.open(filename, "r", "iso8859-1") as csv:
            for line in csv:
                # AT236000000501196215;PAYPAL *TECHNIKWELT
                # 35314369001|85130065041505238623488;12.02.2015;09.02.2015;-46,83;EUR
                try:
                    (konto, buchungstext, zahlung, buchung, betrag, waehrung) = line.split(";")
                    textteile = buchungstext.split("|")
                    text = textteile[0]
                    nummer = textteile[-1]
                    key = (buchung, betrag, text)
                    if key not in buchungen:
                        tokens = re.findall(r'(?ms)\W*(\w+)', text)
                        final_tokens = []
                        for token in tokens:
                            if len(token) <= 2:
                                continue
                            if token not in final_tokens:
                                final_tokens.append(token.lower())
                        buchungen[key] = {
                            "kontonummer" : konto,
                            "bemerkung" : buchungstext,
                            "text" : text,
                            "laufnummer": nummer,
                            "buchungsdatum": buchung,
                            "zahlungsdatum": zahlung,
                            "betrag": float(betrag.replace(".", "").replace(",", ".")),
                            "waehrung": waehrung.strip(),
                            "tokens": final_tokens,
                        }
                        if buchungen[key]["betrag"] > 0.0:
                            final_tokens.append("einnahmen")
                        else:
                            final_tokens.append("ausgaben")
                except ValueError as exc:
                    print(exc)
                    print(filename)
                    print("format error " + line)
                except KeyError as exc:
                    print(exc)
                    print(filename)
                    print("Key error " + line)
    return buchungen

def main():
    # get latest booking available
    latest_booking = gch.get_latest_booking(options.account)
    latest_date = latest_booking["date"]
    latest_number = int(latest_booking["num"])
    print("latest booking found on %s with number %s" % (latest_date, latest_number))
    year, month, day = latest_date.split("-")
    startdate = datetime.date(int(year), int(month), int(day))
    print("searching for split with date > %s" % (startdate))
    # read all available exported lines
    buchungen = bawag_mc_export_reader()
    # read stored data and test some extra stuff
    network1 = Network.from_json(open(options.input_file, "rt").read())
    # iterate through lines
    for nummer, data in buchungen.items():
        day, month, year = data["zahlungsdatum"].split(".")
        date = datetime.date(int(year), int(month), int(day))
        date_str = "%4s-%02s-%02s" % (year, month, day)
        if date <= startdate:
            # print("skipping this split date %s below %s" % (date, startdate))
            continue
        # predict category of split from stored network data
        category = network1.predict(data["tokens"])[1]
        print(category)
        item = {
            "date" : date, # has to be datetime
            "description" : data["bemerkung"].encode("utf-8"), # encode utf-8
            "notes" : "imported %s" % datetime.datetime.now(), # has to be datetime
            "soll" : options.account,
            "soll_value" : data["betrag"],
            "haben" : category.encode("utf-8"), # encode utf-8
            "haben_value" : data["betrag"] * -1,
        }
        # print(item)
        gch.add_transaction(item)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("to import some Bawak-Mastercard export File into gnucash")
    # parser.add_argument("-d", "--date", help="import splits newer than date, format YYYY-MM-DD", required=True)
    parser.add_argument("-g", "--gnucash-file", help="gnucash file to open", required=True)
    parser.add_argument("-i", "--input-file", help="input network state to read", required=True)
    parser.add_argument("-e", "--export-dir", help="export directory with bawag export CSV Files", required=True)
    parser.add_argument("-a", "--account", help="gnucash account to import to", required=True)
    options = parser.parse_args()
    #options = parser.parse_args("-n 8307 -d 2016-05-13".split(" "))
    if not os.path.isfile(options.gnucash_file):
        print("gnucash file %s does not exist" % options.gnucash_file)
        sys.exit(1)
    if not os.path.isfile(options.input_file):
        print("input network file %s does not exist" % options.input_file)
        sys.exit(1)
    if not os.path.isdir(options.export_dir):
        print("export directory %s does not exist" % options.export_dir)
        sys.exit(1)
    #if len(options.date.split("-")) != 3:
    #    print("date %s not in required format YYYY-MM-DD" % options.date)
    #    sys.exit(1)
    gch = GnuCashHelper(options.gnucash_file)
    try:
        main()
    except Exception as exc:
        logging.exception(exc)
    finally:
        gch.end()
