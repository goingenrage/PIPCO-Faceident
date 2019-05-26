# Main goal is to launch this script with defining a directory in which the files are located
# The script then automatically inserts all found pictures into the database

db_directory = '/home/michael/semesterprojekt_test.db'

import os
import sqlite3
from time import sleep

#   Database connection function
#   Returns a connection and a cursor object
def new_database(name):
    con = sqlite3.connect(name)
    cur = con.cursor()
    return con, cur

#   Function to insert an action dataset into the action table in the database if the dataset does not exist
def insertAction(con, cur):
    try:
        select_query = \
            "SELECT count(*) " \
            "FROM Action " \
            "WHERE " \
            "name like '%Email-Benachrichtigung%'"
        insert_query = "INSERT INTO Action(name) VALUES(?)"

        #Execute the select query and check how many lines were affected
        cur.execute(select_query)
        if (cur.fetchone()[0] == 0):
            #If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_query, ['Email-Benachrichtigung'])
            con.commit()
    except Exception as e:
        print(e)


def insert_picture(current_file, cur):
    # Predefine picture insert query
    insert_query = "INSERT INTO Picture(data,type,filename) VALUES(?,?,?)"
    with open(current_file, 'rb') as input_file:

        #Open the file and save the data into ablob variable
        #ext defines the extension of the file (typically the structure ".jpg")
        #afile contains the pure filename, without file extension
        ablob = input_file.read()
        base = os.path.basename(current_file)
        afile, ext = os.path.splitext(base)
        cur.execute(insert_query, [sqlite3.Binary(ablob), ext, afile])
        return cur.lastrowid


if __name__ == "__main__":
    try:
        import sys
        from scripts import interfacedb

        print(sys.argv)
        #Get database connection
        con, cur = new_database(db_directory)
        interfacedb.initialize(db_directory,'/home/michael/tmp/')
        dir_counter = 0
        sub_dir_counter = 0
        directories = os.listdir(sys.argv[1])
        for directory in directories:
            dir_counter += 1
            subdirectories = os.listdir(sys.argv[1] + '/' + directory)
            for subdirectory in subdirectories:
                sub_dir_counter += 1
                # Predefine person insert query
                insert_person_query = "INSERT INTO Person(name, role) VALUES(?,?)"
                parent_dir = sys.argv[1] + '/' + directory + '/' + subdirectory
                files = os.listdir(parent_dir)
                file_ids = []

                #Execute insert_person_query and get the last id of the table, which should be the inserted one
                cur.execute(insert_person_query, [subdirectory,1])
                person_id = cur.lastrowid

                for file in files:
                    # Insert pictures into database and retrieve the id
                    interfacedb.__insert_picture(person_id, parent_dir + '/' + file, cur)

                con.commit()
                print(dir_counter, ".", sub_dir_counter, ": ", subdirectory,
                      " inserted. Now sleeping for 0.15 seconds")
                #To prevent some misbehaviour, sleep 0.15seconds
                sleep(0.15)
    except Exception as e:
        print("\n\n\n", e)
        con.rollback()
