# Main goal is to launch this script with defining a directory in which the files are located
# The script then automatically inserts all found pictures into the database

db_directory = '/home/michael/semesterprojekt.db'

import os
import sqlite3
from time import sleep


def new_database(name):
    con = sqlite3.connect(name)
    cur = con.cursor()
    return con, cur


def insertAction(con, cur):
    try:
        action_query = \
            "SELECT count(*) " \
            "FROM Action " \
            "WHERE " \
            "name like '%Email-Benachrichtigung%'"
        insert_action_query = "INSERT INTO Action(name) VALUES(?)"
        cur.execute(action_query)
        if (cur.fetchone()[0] == 0):
            cur.execute(insert_action_query, ['Email-Benachrichtigung'])
            con.commit()
            print(cur.lastrowid)
    except Exception as e:
        print(e)


def insert_picture(current_file, cur):
    # Predefine picture insert query
    insert_query = "INSERT INTO Picture(data,type,filename) VALUES(?,?,?)"
    with open(current_file, 'rb') as input_file:
        ablob = input_file.read()
        base = os.path.basename(current_file)
        afile, ext = os.path.splitext(base)
        cur.execute(insert_query, [sqlite3.Binary(ablob), ext, afile])
        return cur.lastrowid


if __name__ == "__main__":
    try:
        import sys

        print(sys.argv)
        con, cur = new_database(db_directory)
        insertAction(con, cur)
        dir_counter = 0
        sub_dir_counter = 0
        directories = os.listdir(sys.argv[1])
        for directory in directories:
            dir_counter += 1
            subdirectories = os.listdir(sys.argv[1] + '/' + directory)
            for subdirectory in subdirectories:
                sub_dir_counter += 1
                # Predefine person insert query
                insert_person_query = "INSERT INTO Person(actionid,name) VALUES(?,?)"
                insert_person_picture_query = "INSERT INTO PersonPicture(personid,pictureid) VALUES(?,?)"
                parent_dir = sys.argv[1] + '/' + directory + '/' + subdirectory
                files = os.listdir(parent_dir)
                file_ids = []
                for file in files:
                    # Insert pictures into database and retrieve the id
                    file_ids.append(insert_picture(parent_dir + '/' + file, cur))
                cur.execute(insert_person_query, [1, subdirectory])
                person_id = cur.lastrowid
                for file_id in file_ids:
                    cur.execute(insert_person_picture_query, [person_id, file_id])
                con.commit()
                print(dir_counter, ".", sub_dir_counter, ": ", subdirectory + " inserted with ", len(file_ids),
                      " files inserted. Now sleeping for 0.15 seconds")
                sleep(0.15)
    except Exception as e:
        print("\n\n\n", e)
