#!/usr/bin/python2
# -*- coding: utf-8 -*-
import os
import sys
import codecs
import json
import re
import glob
import datetime
import argparse
import logging
logging.basicConfig(level=logging.DEBUG)
# own modules
from Network import Network as Network
from Categorizer import Categorizer as Categorizer
from GnuCashHelper import GnuCashHelper as GnuCashHelper

# es gibt {'BG', 'VB', 'FE', 'MC', 'VD', 'OG'}
# AT BG FE IG MC OG VB VD
typen_dict = {
    "MC": "Mastercard",
    "OG": "Lastschrift",
    "BG": "Dauerauftrag",
    "FE": "Überweisung",
    "VD": "Gutschrift",
    "VB": "SEPA",
    "NV": "Rücküberweisung",
    "ZE": "Überweisung",
}


def bawag_export_reader():
    """
    read bawag specific export file and return dict
    """
    typen = set() # to find types
    buchungen = {}
    for filename in glob.glob(os.path.join(options.export_dir, "PSK_Umsatzliste_2*.csv")):
        with codecs.open(filename, "r", "iso8859-1") as csv:
            for line in csv:
                #print(line.strip())
                # AT286000000077346089;Zinsen HABEN
                # BG/000003927;03.10.2011;30.09.2011;+2,38;EUR
                try:
                    (konto, bemerkung, buchung, zahlung, betrag, waehrung) = line.split(";")
                    m = re.match("^(.*)([A-Z]{2}/[0-9]{9})(.*)$", bemerkung)
                    if m is not None:
                        referenz = m.group(1).strip()
                        laufnummer = m.group(2).strip()
                        verwendungszweck = m.group(3).strip()
                        typ, nummer = laufnummer.split("/")
                        if int(nummer) not in buchungen:
                            tokens = re.findall(r'(?ms)\W*(\w+)', verwendungszweck)
                            tokens.extend(re.findall(r'(?ms)\W*(\w+)', referenz))
                            tokens.extend(referenz.split(" "))
                            tokens.extend(verwendungszweck.split(" "))
                            final_tokens = []
                            for token in tokens:
                                if len(token) <=2:
                                    continue
                                if token not in final_tokens:
                                    final_tokens.append(token.lower())
                            buchungen[int(nummer)] = {
                                "kontonummer" : konto,
                                "bemerkung" : re.sub( '\s+', ' ', bemerkung).strip(), # remove multiple whitespaces
                                "referenz" : re.sub(" +"," ", referenz),
                                "laufnummer": int(nummer),
                                "verwendungszweck": re.sub(" +"," ", verwendungszweck),
                                "buchungsdatum": buchung,
                                "zahlungsdatum": zahlung,
                                "betrag": float(betrag.replace(".", "").replace(",", ".")),
                                "waehrung": waehrung.strip(),
                                "buchungstyp": typen_dict[typ],
                                "tokens": final_tokens,
                            }
                            if buchungen[int(nummer)]["betrag"] > 0.0:
                                final_tokens.append("einnahmen")
                            else:
                                final_tokens.append("ausgaben")
                            typen.add(typ)
                    else:
                        break
                except ValueError as exc:
                    print(exc)
                    print(filename)
                    print("format error " + line)
                except KeyError as exc:
                    print (exc)
                    print(filename)
                    print("Key error " + line)
    print(typen)
    return buchungen

def main():
    # get latest booking available
    latest_booking = gch.get_latest_booking(options.account)
    latest_date = latest_booking["date"]
    latest_number = int(latest_booking["num"])
    print("latest booking found on %s with number %s" % (latest_date, latest_number))
    year, month, day = latest_date.split("-")
    startdate = datetime.date(int(year), int(month), int(day))
    print("searching for split number > %d and date => %s" % (latest_number, startdate))
    # read all available exported lines
    buchungen = bawag_export_reader()
    # read stored data and test some extra stuff
    network = Network.from_json(open(options.input_file, "rt").read())
    # iterate through lines
    for nummer, data in sorted(buchungen.items()):
        if nummer <= latest_number:
            print("skipping this split number %d below %d" % (nummer, latest_number))
            continue
        day, month, year = data["zahlungsdatum"].split(".")
        date = datetime.date(int(year), int(month), int(day))
        date_str = "%4s-%02s-%02s" % (year, month, day)
        if date <= startdate:
            print("skipping this split date %s below %s" % (date, startdate))
            continue
        # predict category of split from stored network data
        category = network.predict(data["tokens"])[1]
        item = {
            "date" : date, # has to be datetime
            "description" : data["bemerkung"].encode("utf-8"), # encode utf-8
            "notes" : "imported %s" % datetime.datetime.now(), # has to be datetime
            "num" : str(nummer), # has to be str
            "soll" : options.account,
            "soll_value" : data["betrag"],
            "haben" : category.encode("utf-8"), # encode utf-8
            "haben_value" : data["betrag"] * -1,
        }
        #print(item)
        gch.add_transaction(item)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("to import some Bawak export File into gnucash")
    parser.add_argument("-a", "--account", help="account to import to, in dot notation like Aktiva.Konto", required=True)
    parser.add_argument("-g", "--gnucash-file", help="gnucash file to open", required=True)
    parser.add_argument("-i", "--input-file", help="input network state to read", required=True)
    parser.add_argument("-e", "--export-dir", help="export directory with bawag export CSV Files", required=True)
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
    gch = GnuCashHelper(options.gnucash_file)
    try:
        main()
    except Exception as exc:
        logging.exception(exc)
    finally:
        gch.end()
