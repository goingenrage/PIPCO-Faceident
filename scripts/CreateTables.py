import sqlite3
import configparser





def createTables(dbpath):
    # Define the path to the .db-file . If not provided, the file will be created
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()

    # open file, which has to be located within the project dir
    f = open("./files/sql", "r")
    try:
        # split the file at ';'
        splitted = f.read().split(';')

        # for each item in splitted[], the cursor will execute its content
        for split in splitted:
            print(split)
            cursor.execute(split)
    except Exception as e:
        print(e)
    finally:
        f.close()


def closeConnection():
    # close connection and cursor
    cursor.close()
    connection.close()


if __name__ == "__main__":
    config = configparser.RawConfigParser()
    config.read("../config.cfg")
    dbpath = config.get('DEFAULT', 'path_to_database')

    createTables(dbpath)
    closeConnection()
