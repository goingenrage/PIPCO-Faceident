import sqlite3
import os
import time

# region Global variables
__db_location = ""
__tmp_directory = ""
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
    except Exception as e:
        db_location = ""
        tmp_directory = ""
        raise e

#   Checks if the global variables were initialized
#   throws InitializationError if any of the global variables is empty
def __check_for_initialization():
    if not db_location:
        raise Exception("Database location was not initialized. Please call the initialize method first.")
    if not tmp_directory:
        raise Exception("Temporary directory was not initialized. Please call the initialize method first.")
# endregion

# region Misc database functions
def database_connect():
    """
    Verbindet zu der in __db_location angegebenen Datenbank und erstellt ein Connection und ein Cursor Objekt
    :return: con: Connection objekt; cur: Cursor objekt
    """
    con = sqlite3.connect(db_location)
    cur = con.cursor()
    return con, cur

def database_dump(saving_path):
    """
    Exportiert die komplette Datenbank in eine .sql Datei. Der Dateiname enthält das aktuelle Datum sowie die Uhrzeit
    und endet mit 'dump.sql'. Die Datei wird unter dem in saving_path spezifiziertem Pfad zu finden sein
    :param saving_path: Der Pfad, in welchem die Datei gespeichert werden soll.
    """
    try:
        __check_for_initialization()
        timestamp = time.strftime("%d_%m_%Y_%H_%M_%S")
        con, cur = database_connect()
        with open(saving_path+timestamp+'_dump.sql', 'w') as f:
            for line in con.iterdump():
                f.write('%s\n' % line)
    except Exception as e:
        raise e
    finally:
        cur.close()
        con.close()

def database_import(file_path):
    """
    Importiert eine Datenbank dump Datei und führt die in der Datei angegebenen Befehle aus
    :param file_path: Pfad zu der Dump Datei
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        f = open(file_path, 'r')
        str = f.read()
        con.executescript(str)
    except Exception as e:
        raise e
    finally:
        cur.close()
        con.close()
# endregion

# region Reading-functions
def get_by_person(person_name, person_surname=''):
    """
    Sucht anhand der übergebenen Parametern nach Daten in der Datenbank, welche zu dieser Person passen
    :param person_name: Vorname der Person
    :param person_surname: Nachname der Person
    :return: Objekt des Typs PersonWithActions, welche alle in der Datenbank gefundenen Daten enthält.
    """
    try:
        __check_for_initialization()
        sqlPerson = "SELECT id, comment " \
                    "FROM Person " \
                    "WHERE name LIKE :name"

        if person_surname != '':
            sqlPerson = sqlPerson + " AND surname LIKE :surname"
            param = {'name': '%'+person_name+'%', 'surname': '%'+person_surname+'%'}
        else:
            param = {'name': '%' + person_name + '%'}

        connection, cursor = database_connect()
        cursor.execute(sqlPerson, param)
        data_row = cursor.fetchone()
        person_id = data_row[0]
        filenames = __get_pictures_by_personid(person_id)
        actions = __get_actions_by_personid(person_id)
        return DetailedPerson(filenames, person_id, person_name, person_surname, data_row[1], actions)
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

def __get_pictures_by_personid(person_id):
    """
    Sucht anhand der übergebenen Personen ID nach Bildern, welche diese referenzieren.
    Diese werden in einem bestimmten temporären Verzeichnis als .jpg Datei abgelegt.
    :param person_id: Personen ID
    :return: Liste aller Pfade zu den jeweiligen Bildern
    """
    try:
        __check_for_initialization()
        sql = "SELECT data, filename " \
              "FROM Picture " \
              "WHERE personid = :id"
        param = {'id': person_id}

        connection, cursor = database_connect()
        cursor.execute(sql, param)
        data_rows = cursor.fetchall()
        fnames = []
        for data_row in data_rows:
            filename = data_row[1] + '.jpg'
            fnames.append(filename)
            with open(tmp_directory + filename, 'wb') as output_file:
                output_file.write(data_row[0])
        return fnames
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

def __get_actions_by_personid(person_id):
    """
    Sucht in der Datenbank nach Aktionen, welche in der Tabelle PersonAction mit der übergebenen Personen ID übereinstimmen
    :param person_id: Personen ID
    :return: Liste von Namen aller übereinstimmenden Aktionen
    """
    try:
        __check_for_initialization()
        sql = "SELECT Action.name " \
              "FROM Action " \
              "INNER JOIN PersonAction ON Action.id = PersonAction.actionid " \
              "WHERE PersonAction.personid = :id"
        param = {'id': person_id}

        connection, cursor = database_connect()
        cursor.execute(sql, param)
        data_rows = cursor.fetchall()
        anames = []
        for data_row in data_rows:
            anames.append(data_row[0])
        return anames
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

def get_all_persons():
    """
    Gibt alle in der Datenbank vorhandenen Personen mit deren Attributen zurück
    :return: Liste mit Personen-Objekten
    """
    try:
        __check_for_initialization()
        sql = "SELECT id, name, surname, comment " \
              "FROM Person "

        connection, cursor = database_connect()
        cursor.execute(sql)
        data_rows = cursor.fetchall()
        person_list = []
        for data_row in data_rows:
            person_list.append(Person(data_row[0], data_row[1], data_row[2], data_row[3]))
        return person_list
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

def get_all_actions():
    """
    Gibt alle in der Datenbank vorhandenen Aktionen zurück
    :return: Liste mit Aktions-Objekten
    """
    try:
        __check_for_initialization()
        sql = "SELECT id, name " \
              "FROM Action "

        connection, cursor = database_connect()
        cursor.execute(sql)
        data_rows = cursor.fetchall()
        action_list = []
        for data_row in data_rows:
            action_list.append(Action(data_row[0], data_row[1]))
        return action_list
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

def __get_personid_by_name(person_name, person_surname=''):
    """
    Sucht in der Datenbank nach einem Eintrag mit Übereinstimmung mit den Parametern. Wird ein Eintrag gefunden, so wird die ID des Eintrags zurückgegeben.
    :param person_name: Vorname der Person
    :param person_surname: Nachname der Person. Default=''
    :return: Person ID aus der Datenbank
    """
    try:
        __check_for_initialization()
        sql =   "SELECT id " \
                "FROM Person " \
                "WHERE name LIKE :person_name"
        if person_surname != '':
            sql += " AND surname LIKE :person_surname"
            param = {'person_name': '%'+person_name+'%', 'person_surname': '%'+person_surname+'%'}
        else:
            param = {'person_name': '%'+person_name+'%'}

        connection, cursor = database_connect()
        cursor.execute(sql, param)
        return cursor.fetchone()[0]
    except Exception as e:
        raise e

def __get_actionid_by_name(action_name):
    """
    Sucht in der Datenbank nach einer Aktion mit dem Namen wie action_name. Wird ein Eintrag gefunden, so wird dessen ID zurückgegeben.
    :param action_name: Name der Aktion
    :return: ID des passenden Eintrags
    """
    try:
        __check_for_initialization()
        sql =   "SELECT id " \
                "FROM Action " \
                "WHERE name LIKE :action_name"

        param = {'action_name': '%'+action_name+'%'}

        connection, cursor = database_connect()
        cursor.execute(sql, param)
        return cursor.fetchone()[0]
    except Exception as e:
        raise e

def get_all_pictures():
    try:
        __check_for_initialization()
        sql = "SELECT Picture.data, Picture.filename, Person.name " \
              "FROM Picture " \
                "INNER JOIN Person ON Person.id=Picture.personId "

        connection, cursor = database_connect()
        cursor.execute(sql)
        data_rows = cursor.fetchall()
        file_list = []
        person = ''
        for data_row in data_rows:
            if person != data_row[2]:
                person = data_row[2]
                i=1
            filename = person + '.' + str(i) + '.jpg'
            i=i+1
            file_list.append(tmp_directory + filename)
            with open(tmp_directory + filename, 'wb') as output_file:
                output_file.write(data_row[0])
        return file_list
    except Exception as e:
        raise e
    finally:
        cursor.close()
        connection.close()

# endregion

#region Delete-functions
def delete_person_by_name(person_name, person_surname=''):
    """
    Löscht einen Eintrag in der Person Tabelle anhand der Parameter person_name und person_surname.
    Dabei werden auch alle Referenzen auf diesen Eintrag aus Picture und PersonAction gelöscht.
    :param person_name: Vorname der Person
    :param person_surname: Nachname der Person. Default =''
    """
    try:
        __check_for_initialization()
        sql =   "DELETE " \
                "FROM Person " \
                "WHERE id=:person_id"
        person_id = __get_personid_by_name(person_name, person_surname)
        param = {'person_id': person_id}
        connection, cursor = database_connect()
        __delete_images_by_personid(person_id, cursor)
        __delete_person_action_by_personid(person_id, cursor)
        cursor.execute(sql, param)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

def delete_images_by_personid(person_id):
    """
    Löscht jeden Eintrag aus der Tabelle Picture, welche die Personen ID peron_id referenziert.
    Der Vorgang wird hierbei durch eine Transaktion gesichert.
    :param person_id: Personen ID
    """
    try:
        __check_for_initialization()

        sql_del_pic =   "DELETE " \
                        "FROM Picture " \
                        "WHERE personid=:person_id"
        param = {'person_id': person_id}
        connection, cursor = database_connect()
        cursor.execute(sql_del_pic, param)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

def __delete_images_by_personid(person_id, cur):
        """
        Löscht jeden Eintrag aus der Tabelle Picture, welche die Personen ID peron_id referenziert.
        :param person_id: Personen ID
        """
        __check_for_initialization()

        sql_del_pic = "DELETE " \
                      "FROM Picture " \
                      "WHERE personid=:person_id"
        param = {'person_id': person_id}
        cur.execute(sql_del_pic, param)

def delete_person_action_by_personid(person_id):
    """
    Löscht Einträge aus der PersonAction Tabelle, welche die Personen ID person_id besitzen.
    Das Löschen wird per Transaktion gesichert.
    :param person_id: Personen ID
    """
    try:
        __check_for_initialization()
        sql = "DELETE " \
              "FROM PersonAction " \
              "WHERE personid=:person_id"
        param = {'person_id': person_id}
        connection, cursor = database_connect()
        cursor.execute(sql, param)
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

def __delete_person_action_by_personid(person_id, cur):
    """
    Löscht Einträge aus der PersonAction Tabelle, welche die Personen ID person_id besitzen.
    Das Löschen wird nicht abgesichert und es werden keine geworfenen Fehler behandelt.
    :param person_id: Personen ID
    """
    __check_for_initialization()
    sql = "DELETE " \
          "FROM PersonAction " \
          "WHERE personid=:person_id"
    param = {'person_id': person_id}
    cur.execute(sql, param)

def delete_action_by_name(action_name):
    """
    Löscht in der Datenbank den Einträge, welche den Namen wie der Parameter haben.
    :param action_name: Name der zu löschenden Aktion
    """
    try:
        __check_for_initialization()
        sql = "DELETE " \
              "FROM Action " \
              "WHERE id=:action_id"
        action_id = __get_actionid_by_name(action_name)
        param = {'action_id': action_id}
        connection, cursor = database_connect()
        cursor.execute(sql, param)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
#endregion

# region Insert-functions
def insert_action(action_name):
    """
    Legt eine neue Aktion in der Datenbank an. Wenn bereits ein Eintrag mit dem Namen vorhanden ist, wird eine Exception geworfen.
    :param action_name: Name der anzulegenden Aktion
    :return: ID der angelegten Aktion
    """
    try:
        __check_for_initialization()
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
    except Exception as e:
        con.rollback()
        raise e

def insert_person(person_name, person_surname = '', comment=''):
    """
    Legt eine neue Person mit den notwendigen Daten in der Datenbank an.
    Ist durch eine Transaktion gesichert. Ist der Name bereits in der Datenbank vorhanden, so wird eine Exception geworfen.
    :param person_name: Name der Person
    :param person_surname: Nachname der Person. Default=''
    :param comment: Kommentar zum Eintrag. Default=''
    :return: ID des angelegten Eintrags zur Person
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        sql =   "SELECT COUNT(*)" \
                "FROM Person " \
                "WHERE name LIKE :person_name"
        insert_sql = "INSERT INTO Person(name, surname, comment) VALUES(?,?,?)"

        if person_surname != '':
            sql = sql + " AND surname LIKE :person_surname"
            param = {'person_name': '%' + person_name + '%', 'person_surname': '%' + person_surname + '%'}
        else:
            param = {'person_name': '%' + person_name + '%'}

        #Execute the select query and check how many lines were affected
        cur.execute(sql,param)
        if (cur.fetchone()[0] == 0):
            #If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_sql, [person_name,person_surname,comment])
            con.commit()
        else:
            raise Exception(person_name + " already exists in the specified database")
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e

def insert_person_action(person_id, action_id):
    """
    Legt einen neuen Eintrag in der Tabelle PersonAction an
    :param person_id: Personen ID
    :param action_id: Aktions ID
    :return: ID des angelegten Eintrags
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        sql =   "SELECT COUNT(*)" \
                "FROM PersonAction " \
                "WHERE actionid LIKE :action_id " \
                "AND personid LIKE :person_id"
        param = {'action_id': action_id, 'person_id': person_id}
        insert_sql = "INSERT INTO PersonAction(personid, actionid) VALUES(?,?)"

        #Execute the select query and check how many lines were affected
        cur.execute(sql,param)
        if (cur.fetchone()[0] == 0):
            #If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_sql, [person_id, action_id])
            con.commit()
        else:
            raise Exception("This assignment already exists in the specified database")
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e


def insert_picture(personId, file):
    try:
        __check_for_initialization()
        con, cur = database_connect()

        insert_sql = "INSERT INTO Picture(personid,data,filename) VALUES(?,?,?)"

        #Execute the select query and check how many lines were affected

        with open(file, 'rb') as input_file:
            # Open the file and save the data into ablob variable
            # ext defines the extension of the file (typically the structure ".jpg")
            # afile contains the pure filename, without file extension
            ablob = input_file.read()
            base = os.path.basename(file)
            afile, ext = os.path.splitext(base)
            cur.execute(insert_sql, [personId, sqlite3.Binary(ablob), afile])

        con.commit()
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e

def __insert_picture(personId, file, cur):
    try:
        __check_for_initialization()

        insert_sql = "INSERT INTO Picture(personid,data,filename) VALUES(?,?,?)"

        #Execute the select query and check how many lines were affected

        with open(file, 'rb') as input_file:
            # Open the file and save the data into ablob variable
            # ext defines the extension of the file (typically the structure ".jpg")
            # afile contains the pure filename, without file extension
            ablob = input_file.read()
            base = os.path.basename(file)
            afile, ext = os.path.splitext(base)
            cur.execute(insert_sql, [personId, sqlite3.Binary(ablob), afile])

        return cur.lastrowid
    except Exception as e:
        raise e

# endregion

#region Update-functions
def update_person(person_id, person_name, person_surname='', person_comment=''):
    """
    Aktualisiert einen Personen Eintrag anhand ihrer ID mit den als Parametern übergebenen Werten
    :param person_id: ID der zu verändernden Person
    :param person_name: Name der Person
    :param person_surname: Nachname der Person (Default='')
    :param person_comment: Kommentar zur Person (Default='')
    :return: True, falls keine Fehler aufgetreten sind
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        params = {'person_name': person_name, 'id': person_id}
        sql = "UPDATE Person " \
              "SET name = :person_name"
        if person_surname != '':
            sql += ", surname = :person_surname"
            params['person_surname'] = person_surname
        if person_comment != '':
            sql += ", comment = :person_comment"
            params['person_comment'] = person_comment

        sql += " WHERE id = :id"



        # Execute the select query and check how many lines were affected
        cur.execute(sql, params)
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        raise e

def update_action(action_id, action_name):
    """
    Aktualisiert einen Eintrag in der Aktion Tabelle anhand der ID mit dem Parameter als neuen Namenswert
    :param action_id: ID der zu ändernden Aktion
    :param action_name: Neuer Name für die Aktion
    :return: True, falls Änderungen ohne Fehler durchgeführt werden konnten
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        sql = "UPDATE Action " \
              "SET name = :action_name " \
              "WHERE id = :action_id"

        params = {'action_id': action_id, 'action_name': action_name}


        # Execute the select query and check how many lines were affected
        cur.execute(sql, params)
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        raise e
#endregion

#region Classes
class Person:
    def __init__(self, id, name, surname, comment):
        self.id = id
        self.name = name
        self.surname = surname
        self.comment = comment

class DetailedPerson(Person):

    def __init__(self, filenames, id, name, surname, comment, actions):
        self.actions = actions
        self.filenames = filenames
        Person(id, name,surname,comment)

class Action:
    def __init__(self, id, name):
        self.id = id
        self.name = name
#endregion