DEBUG = True

import MySQLdb as _mysql

class MySQLDatabase:
    def __init__ (self, database_name, username, password, host='localhost') :
        try:
            self.db = _mysql.connect(db=database_name,
                                     host=host,
                                     user=username,
                                     passwd=password)
            self.database_name=database_name
            if DEBUG:
                print "Connected to MySQL!"
        except _mysql.Error, e:
            print e

    # Close
    def __del__( self ):
        if hasattr(self, 'db'): # close our connection to free it up in the pool
            self.db.close()
            if DEBUG:
                print "MySQL Connection closed"


    # Get followers from DB
    def get_followers(self):
        result = []
        sql = "SELECT screen_name FROM followers;"
        cursor = self.db.cursor()
        cursor.execute(sql)
        for item in cursor.fetchall():
            result.append(item[0])
        return result


    # Insert followers into DB
    def insert_followers(self, followers):
        for item in followers:
            sql = "INSERT INTO followers (screen_name) VALUES ('"+str(item)+"');"
            if DEBUG:
                print sql
            cursor = self.db.cursor()
            cursor.execute(sql)
        self.db.commit()

