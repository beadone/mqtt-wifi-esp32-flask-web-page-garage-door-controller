

import sqlite3
 
# Connecting to sqlite
# connection object
connection_obj = sqlite3.connect('myhab.db')
 
# cursor object
cursor_obj = connection_obj.cursor()
 
# Drop the GEEK table if already exists.
cursor_obj.execute("DROP TABLE IF EXISTS User")
 
# Creating table
table = """ CREATE TABLE User (
            Id INTEGER PRIMARY KEY,
            username VARCHAR(20) NOT NULL,
            password  VARCHAR(80) NOT NULL,
            last_seen DATETIME
        ); """
 
cursor_obj.execute(table)
 
print("Table is Ready")
 
# Close the connection