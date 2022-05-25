import sqlite3
import argparse
from traceback import format_tb

class MagicPhoneDB():
    """
        There is a SQLite db that contains all sounds
        And now it also contains status and probably settings later on
        The db has all of the sounds in it. There is a preprocess.py script that will take the master sounds and process them into directories to be played
        Eventually I need to give some thought to security, since you might be able to inject commands into this pretty easily

        After reading https://www.sqlite.org/atomiccommit.html I'm really not that concerned with running sync commands, etc to prevent db corruption, seems taken care of

        This is basically a modified copy of what's on the pi
    """

    def __init__ (self):

        # Connect to the SQLite database
        self.DBPath = 'sounds.sqlite'
        self.DBConn = sqlite3.connect(database=self.DBPath, check_same_thread=False)

    def DoQuery(self, query):
        """
            Do a database query, return raw rows
        """

        try:

            DBCursor = self.DBConn.cursor()
            DBCursor.execute(query)

            Rows = DBCursor.fetchall()
            if len(Rows) == 0:
                return None
            else:
                return Rows


        # log exception in the main.log
        except Exception as e:
            print('Database error. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))
            return None


    def FieldNamesForTable(self, table):
        """
            Return a dict of sound table field names to ids for later use for selecting fields by name
            Best solution I could find. Otherwise if I make any changes to field names it won't propagate into the objects
        """

        try:

            DBFieldsCursor = self.DBConn.cursor()
            DBFieldsCursor.execute(f'select * from {table}')
            DBFields = {}
            DBFieldIndex = 0
            for FieldName in DBFieldsCursor.description:
                DBFields[FieldName[0]] = DBFieldIndex
                DBFieldIndex += 1
            del(DBFieldsCursor)
            return DBFields


        # log exception in the main.log
        except Exception as e:
            print('Database error. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))
            return None


    def DoCommit(self):
        """
            Do a database commit. 
        """

        try:
            self.DBConn.commit()

        # log exception in the main.log
        except Exception as e:
            print('Database error. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))


# Instantiate
conn = MagicPhoneDB()

# This provides a way to run sql from cli
# This was super helpful: https://docs.python.org/3/howto/argparse.html#id1
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='The database query to run.')
    args = parser.parse_args()

    print(args.query)
    print(conn.DoQuery(args.query))
    conn.DoCommit()