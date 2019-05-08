import sqlite3
import os

# region Global variables
db_location = ""
tmp_directory = ""
# endregion

# region Initialization
#   Initialization function. Sets the database_location and the temporary_saving_directory
#   Params:    database_location (eg. /home/michael/semesterprojekt.db)
#              temporary_saving_directory (eg. /home/michael/tmp/)
def initialize(database_location, temporary_saving_directory):
    try:
        global db_location
        global tmp_directory

        db_location = database_location
        tmp_directory = temporary_saving_directory
    except:
        db_location = ""
        tmp_directory = ""
        pass


#   Checks if the global variables were initialized
#   throws InitializationError if any of the global variables is empty
def check_for_initialization():
    if not db_location:
        raise InitializationError("Database location was not initialized. Please call the initialize method first.")
    if not tmp_directory:
        raise InitializationError("Temporary directory was not initialized. Please call the initialize method first.")
# endregion

# region Database connection
#   Database connection function
#   Returns a connection and a cursor object
def database_connect():
    con = sqlite3.connect(db_location)
    cur = con.cursor()
    return con, cur
# endregion

# region Reading-functions
#Gets image data, extension, filename and the corresponding persons name from a database located in database_location
#Saves every image in a given temporary_saving_directory
#returns an array with the directory to the output files
def get_all_images_with_person():
    try:
        check_for_initialization()
        sql = "SELECT Picture.data, Picture.type, Picture.filename, Person.name " \
              "FROM Picture " \
              "INNER JOIN PersonPicture ON Picture.id = PersonPicture.pictureid " \
              "INNER JOIN Person ON PersonPicture.personid = Person.id "
        connection, cursor = database_connect()
        cursor.execute(sql)
        data_rows = cursor.fetchall()
        fnames = []
        for data_row in data_rows:
            filename = data_row[2] + data_row[1]
            fnames.append(filename)
            with open(tmp_directory + filename, 'wb') as output_file:
                output_file.write(data_row[0])
        return fnames
    except:
        pass
    finally:
        cursor.close()
        connection.close()
# endregion

# region Delete-functions
# Deletes every database entry related to the given person
# Param:    person_name = name of the person. Has to be the same as in the database
def delete_images_by_person_name(person_name):
    try:
        check_for_initialization()
        sql = "SELECT PersonPicture.personid, PersonPicture.pictureid " \
              "FROM PersonPicture " \
              "INNER JOIN Person ON PersonPicture.personid = Person.id " \
              "WHERE Person.name LIKE :name"

        sql_del_pic =   "DELETE " \
                        "FROM Picture " \
                        "WHERE id=:id"

        sql_del_per =   "DELETE " \
                        "FROM Person " \
                        "WHERE id=:id"

        sql_del_perpic =    "DELETE " \
                            "FROM PersonPicture " \
                            "WHERE personid=:perid " \
                            "AND pictureid=:picid"

        param = {'name': '%'+person_name+'%'}
        connection, cursor = database_connect()
        cursor.execute(sql, param)
        data_rows = cursor.fetchall()
        person_id=0
        for data_row in data_rows:
            person_id = data_row[0]
            if data_row[1] != 0:
                picture_id = data_row[1]
                param_del_perpic = {'perid': person_id, 'picid': picture_id}
                param_del_pic = {'id': picture_id}

                cursor.execute(sql_del_perpic, param_del_perpic)
                cursor.execute(sql_del_pic, param_del_pic)
        param_del_per = {'id': person_id}
        cursor.execute(sql_del_per,param_del_per)

        connection.commit()
    except:
        connection.rollback()
        pass
    finally:
        cursor.close()
        connection.close()
# endregion

# region Insert-functions
def insert_action(action_name):
    try:
        check_for_initialization()
        con, cur = database_connect()
        sql =   "SELECT count(*) " \
                "FROM Action " \
                "WHERE name like :action_name"

        params = {'action_name': '%'+action_name+'%'}
        insert_query = "INSERT INTO Action(name) VALUES(?)"

        #Execute the select query and check how many lines were affected
        cur.execute(sql,params)
        if (cur.fetchone()[0] == 0):
            #If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_query, [action_name])
            con.commit()
        else:
            raise Exception(action_name+" already exists in the specified database")
        return cur.lastrowid
    except:
        con.rollback()
        pass

def insert_person(person_name):
    try:
        check_for_initialization()
        con, cur = database_connect()
        sql =   "SELECT COUNT(*)" \
                "FROM Person" \
                "WHERE name LIKE :person_name"
        insert_sql = "INSERT INTO Person(name) VALUES(?)"

        params = {'person_name': '%' + person_name + '%'}

        #Execute the select query and check how many lines were affected
        cur.execute(sql,params)
        if (cur.fetchone()[0] == 0):
            #If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_sql, [person_name])
            con.commit()
        else:
            raise Exception(person_name + " already exists in the specified database")
        return cur.lastrowid
    except:
        con.rollback()
        pass

# def insert_picture(file, cur):
#     # Predefine picture insert query
#     insert_query = "INSERT INTO Picture(data,type,filename) VALUES(?,?,?)"
#     with open(file, 'rb') as input_file:
#
#         #Open the file and save the data into ablob variable
#         #ext defines the extension of the file (typically the structure ".jpg")
#         #afile contains the pure filename, without file extension
#         ablob = input_file.read()
#         base = os.path.basename(file)
#         afile, ext = os.path.splitext(base)
#         cur.execute(insert_query, [sqlite3.Binary(ablob), ext, afile])
#         return cur.lastrowid
# endregion

class InitializationError(Exception):
    pass