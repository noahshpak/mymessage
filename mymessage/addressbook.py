import sys
import os
import sqlite3
from pprint import pprint

class AddressBook(object):

    def __init__(self):
        self.full_address_book = self.query("")


    def query_number(self, number):
        return " ".join(self.full_address_book[self.clean_number(number)][:2])

    def query_email(self, email):
        res = self.query(email)
        if res:
            for k in res.keys():
                return " ".join(res[k][:2])
        else:
            return ""

    def query(self, keyword):
        out = output(self.query_db(keyword))
        return out

    def query_db(self, keyword):
        """Query the address book for keyword and return the results as a list of
        tuples.
        """
        sources = os.listdir(os.path.expanduser("~/Library/Application Support/AddressBook/Sources"))
        rows = []

        for source in sources:
            if source != '.DS_Store':
                newrows = self.query_source_db(keyword, os.path.expanduser(os.path.join("~/Library/Application Support",
                    "AddressBook/Sources", source, "AddressBook-v22.abcddb")))

                for row in newrows:
                    rows.append(row)
        return rows

    def query_source_db(self, keyword, database):
        connection = sqlite3.connect(database)
        c = connection.cursor()
        k = ("%%%s%%" % keyword.decode("utf-8"),) * 5
        c.execute("""SELECT ZABCDEMAILADDRESS.ZADDRESS, ZABCDRECORD.ZTITLE,
                  ZABCDRECORD.ZFIRSTNAME, ZABCDRECORD.ZMIDDLENAME,
                  ZABCDRECORD.ZLASTNAME, ZABCDRECORD.ZSUFFIX,
                  ZABCDRECORD.ZORGANIZATION, ZABCDRECORD.ZDISPLAYFLAGS, ZABCDPHONENUMBER.ZFULLNUMBER, ZABCDEMAILADDRESS.ZOWNER
                  FROM ZABCDPHONENUMBER
                  LEFT OUTER JOIN ZABCDRECORD
                  ON ZABCDPHONENUMBER.ZOWNER = ZABCDRECORD.Z_PK
                  LEFT OUTER JOIN ZABCDEMAILADDRESS
                  ON ZABCDPHONENUMBER.ZOWNER  = ZABCDEMAILADDRESS.ZOWNER
                  WHERE ZABCDEMAILADDRESS.ZADDRESS LIKE ?
                  OR ZABCDRECORD.ZFIRSTNAME LIKE ?
                  OR ZABCDRECORD.ZMIDDLENAME LIKE ?
                  OR ZABCDRECORD.ZLASTNAME LIKE ?
                  OR ZABCDRECORD.ZORGANIZATION LIKE ?

                    """, k)
        #rows = zip(rows,[number for number in c])
        rows = [row for row in c]

        return rows

    @staticmethod
    def clean_number(phone):
        return phone.replace('(', '').replace(' ', '').replace('-', '').replace(')', '').replace('+', '')



def output(results):
    """Take the list of results and print it as per mutt's expected output"""
    address_book = dict(zip([AddressBook.clean_number(row[8]) for row in results], [[format(r[2]),format(r[4]),str(r[0])] for r in results]))
    #pprint(address_book)
    return address_book

if __name__ == "__main__":
    print AddressBook().query_number(u"+12024892355")