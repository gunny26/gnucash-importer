#!/usr/bin/python2
# -*- coding: utf-8 -*-
# gnucash imports
import sys
import json
import datetime
import re
import logging
from gnucash import Session, Transaction, Split, GncNumeric


class GnuCashHelper(object):
    """some hany functions around gnucash api"""

    def __init__(self, filename):
        self.__session = Session(filename, is_new=False)
        self.__book = self.__session.book

    def account_from_path(self, top_account, account_path, original_path=None):
        if original_path is None:
            original_path = account_path
        account, account_path = account_path[0], account_path[1:]
        account = top_account.lookup_by_name(account)
        #print(account.name)
        if account.get_instance() is None:
            raise Exception(
                "path " + ''.join(original_path) + " could not be found")
        if len(account_path) > 0:
            return self.account_from_path(account, account_path, original_path)
        else:
            return account

    def lookup_account(self, root, name):
        path = name.split('.')
        return self.lookup_account_by_path(root, path)

    def lookup_account_by_path(self, root, path):
        acc = root.lookup_by_name(path[0])
        if acc.get_instance() == None:
            raise Exception('Account path {} not found'.format('.'.join(path)))
        if len(path) > 1:
            return self.lookup_account_by_path(acc, path[1:])
        return acc

    def get_root(self):
        return self.__book.get_root_account()

    @staticmethod
    def tokenizer(entry, blacklist_tokens=None):
        """
        cut string into tokens
        entry has to be in gnucach entry data format
        """
        # like {'haben': 'Ausgleichskonto-EUR', 'soll':
        # 'Aktiva.PSK-Konto', 'num': '', 'description': 'Abgleich',
        # 'date': '2000-01-01', 'haben_value': '3002.63', 'notes':
        # 'None', 'soll_value': '-3002.63'}
        if blacklist_tokens is None:
            blacklist_tokens = []
        tokens = re.findall(r'(?ms)\W*(\w+)', entry["description"])
        tokens.extend(re.findall(r'(?ms)\W*(\w+)', entry["notes"]))
        tokens.extend(entry["description"].split(" "))
        tokens.extend(entry["notes"].split(" "))
        final_tokens = []
        for token in tokens:
            if len(token) <= 2:
                continue
            if token not in final_tokens:
                final_tokens.append(token.lower())
            # find some subtokens from  og/123762137
            for subtoken in token.split("/"):
                if subtoken not in final_tokens:
                    final_tokens.append(subtoken)
        if entry["soll_value"] > 0.0:
            final_tokens.append("einnahmen")
        else:
            final_tokens.append("ausgaben")
        return entry["haben"], [token for token in final_tokens if token not in blacklist_tokens]

    def gnucash_export(self, path):
        """
        export all splits of particular account given by path
        path should be joined by .
        """
        account_path = path.split(".")
        try:
            root_account = self.get_root()
            print(root_account.name)
            orig_account = self.account_from_path(root_account, account_path)
            # help(orig_account)
            # print(orig_account)
            print(orig_account.name)
            # print(orig_account.get_instance())
            print(orig_account.get_full_name())
            for split in orig_account.GetSplitList():
                other = split.GetOtherSplit()
                if other is None:
                    print("there is not other account")
                    sys.exit(2)
                other_account = other.GetAccount()
                if other_account is None:
                    print("No other account found")
                    sys.exit(1)
                other_name = other_account.get_full_name()
                other_value = other.GetValue()
                # 01.02.2012;Internet;;36336 00007727621 Walter oder Monika
                # Schick;Internet FE/000004174;;PSK-Konto;T;;N;15,50 ;;15,50;;;
                # get transaction to witch split belongs
                # a transaction consists of 1..n splits
                trans = split.parent
                if len(trans.GetSplitList()) > 2:
                    print("there are more than 2 accounts involved, not supported")
                    sys.exit(3)
                csv_line = {
                 "soll" : orig_account.get_full_name(),
                 "haben" : other_name,
                 "date" : str(datetime.date.fromtimestamp(trans.GetDate())),
                 "description" : str(trans.GetDescription()),
                 "notes" : str(trans.GetNotes()),
                 "num" : str(trans.GetNum()),
                 "soll_value" : str(split.GetValue()),
                 "haben_value" : str(other_value),
                }
                yield csv_line
                #print(json.dumps(csv_line, indent=4))
                #for tsplit in trans.GetSplitList():
                #    account = tsplit.GetAccount()
                #    account_name = str(account.GetName())
                #    value = str(tsplit.GetValue())
        except Exception as exc:
            logging.exception(exc)

    def get_latest_booking(self, path):
        """
        return latest booking of this particular account
        """
        account_path = path.split(".")
        try:
            root_account = self.get_root()
            print(root_account.name)
            orig_account = self.account_from_path(root_account, account_path)
            # help(orig_account)
            # print(orig_account)
            print(orig_account.name)
            # print(orig_account.get_instance())
            print(orig_account.get_full_name())
            split = orig_account.GetSplitList()[-1]
            other = split.GetOtherSplit()
            if other is None:
                print("there is not other account")
                sys.exit(2)
            other_account = other.GetAccount()
            if other_account is None:
                print("No other account found")
                sys.exit(1)
            other_name = other_account.get_full_name()
            other_value = other.GetValue()
            # 01.02.2012;Internet;;36336 00007727621 Walter oder Monika
            # Schick;Internet FE/000004174;;PSK-Konto;T;;N;15,50 ;;15,50;;;
            # get transaction to witch split belongs
            # a transaction consists of 1..n splits
            trans = split.parent
            if len(trans.GetSplitList()) > 2:
                print("there are more than 2 accounts involved, not supported")
                sys.exit(3)
            csv_line = {
             "soll" : orig_account.get_full_name(),
             "haben" : other_name,
             "date" : str(datetime.date.fromtimestamp(trans.GetDate())),
             "description" : str(trans.GetDescription()),
             "notes" : str(trans.GetNotes()),
             "num" : str(trans.GetNum()),
             "soll_value" : str(split.GetValue()),
             "haben_value" : str(other_value),
            }
            return csv_line
        except Exception as exc:
            logging.exception(exc)

    def add_transaction(self, item):
        """
        add new transaction
        item must have following keys
        """
        assert "date" in item.keys()
        assert "description" in item.keys()
        assert "notes" in item.keys()
        assert "soll" in item.keys()
        assert "soll_value" in item.keys()
        assert "haben" in item.keys()
        assert "haben_value" in item.keys()
        commod_tab = self.__book.get_table()
        currency = commod_tab.lookup('ISO4217', "EUR")
        logging.info('Adding transaction for account "%s" (%s %s)..', item["soll"], item["soll_value"],
                     currency.get_mnemonic())
        root = self.__book.get_root_account()
        tx = Transaction(self.__book)
        tx.BeginEdit()
        tx.SetCurrency(currency)
        tx.SetDateEnteredTS(datetime.datetime.now())
        tx.SetDatePostedTS(item["date"])
        tx.SetDescription(item["description"])
        tx.SetNotes(item["notes"])
        if "num" in item.keys():
            tx.SetNum(item["num"])
        # soll
        #acc = self.lookup_account(root, item["soll"])
        acc = self.account_from_path(self.get_root(), item["soll"].split("."))
        s1 = Split(self.__book)
        s1.SetParent(tx)
        s1.SetAccount(acc)
        amount = int(item["soll_value"] * currency.get_fraction())
        s1.SetValue(GncNumeric(amount, currency.get_fraction()))
        s1.SetAmount(GncNumeric(amount, currency.get_fraction()))
        # haben
        # acc2 = self.lookup_account(root, item["haben"])
        acc2 = self.account_from_path(self.get_root(), item["haben"].split("."))
        s2 = Split(self.__book)
        s2.SetParent(tx)
        s2.SetAccount(acc2)
        amount = int(item["haben_value"] * currency.get_fraction())
        s2.SetValue(GncNumeric(amount, currency.get_fraction()))
        s2.SetAmount(GncNumeric(amount, currency.get_fraction()))
        tx.CommitEdit()

    def end(self):
        """should be always called to prevent locking"""
        self.__session.end()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    gch = GnuCashHelper("gnucash_sqlite/psk_konto_sqlite.gnucash")
    for entry in gch.gnucash_export("Aufwendungen.Büro & Bücher.LIBRO"):
        print(json.dumps(entry, indent=4))
    gch.end()
