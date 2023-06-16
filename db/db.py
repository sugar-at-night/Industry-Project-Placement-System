import mysql.connector
from . import connect
# import connect

def get_connection():
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass, host=connect.dbhost,
                                         database=connect.dbname, port=connect.dbport)
    return connection


def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass, host=connect.dbhost,
                                         database=connect.dbname, port=connect.dbport, autocommit=True)
    dbconn = connection.cursor(buffered=True) # set buffered to True, so that I could use functions like lastrowid directly
    dbconn.execute('SET NAMES utf8mb4') # set encoding to utf8mb4
    return dbconn
