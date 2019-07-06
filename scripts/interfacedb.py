import sqlite3
import os
import time

# region Initialization


def initialize(database_location, temporary_saving_directory):
    """
    Initialisierungsfunktion. Setzt die beiden Variablen db_location und tmp_directory
    :param database_location: Pfad zur Datenbankdatei (z.B. '/home/m/semesterprojekt.db')
    :param temporary_saving_directory: Pfad zum temporären Speicherverzeichnis (z.B. '/home/m/tmp/')
    :return: True, falls keine Fehler aufgetreten sind
    """
    try:
        global db_location
        global tmp_directory

        db_location = database_location
        tmp_directory = temporary_saving_directory
    except Exception as e:
        db_location = ""
        tmp_directory = ""
        raise e
    finally:
        return True


def __check_for_initialization():
    """
    Prüft ob die beiden globalen Variablen initialisiert wurden. Falls nicht wird eine entsprechende Exception geworfen.
    :return: True, falls keine Fehler aufgetreten sind
    """
    if not db_location:
        raise Exception("Database location was not initialized. Please call the initialize method first.")
    if not tmp_directory:
        raise Exception("Temporary directory was not initialized. Please call the initialize method first.")
    return True


def check_for_initialization():
    """
    Prüft ob die beiden globalen Variablen initialisiert wurden. Falls nicht wird eine entsprechende Exception geworfen.
    Methode ist nur vorhanden, damit sie im Unittest explizit getestet werden kann.
    :return: True, falls keine Fehler aufgetreten sind
    """
    if not db_location:
        raise Exception("Database location was not initialized. Please call the initialize method first.")
    if not tmp_directory:
        raise Exception("Temporary directory was not initialized. Please call the initialize method first.")
    return True
# endregion


# region DB-Connect, Dump, Import
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
    :return: fname: Dateipfad zu dem erstellten SQL-file
    """
    try:
        __check_for_initialization()
        timestamp = time.strftime("%d_%m_%Y_%H_%M_%S")
        con, cur = database_connect()
        fname = saving_path+timestamp+'_dump.sql'
        with open(fname, 'w') as f:
            for line in con.iterdump():
                f.write('%s\n' % line)

        return fname
    except Exception as e:
        raise e
    finally:
        cur.close()
        con.close()


def database_import(file_path):
    """
    Importiert eine Datenbank dump Datei und führt die in der Datei angegebenen Befehle aus
    :param file_path: Pfad zu der Dump Datei
    :return: True, falls keine Fehler aufgetreten sind
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        f = open(file_path, 'r')
        filestring = f.read()
        con.executescript(filestring)

        return True
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
    :param person_surname: Nachname der Person (Default='')
    :return: Objekt des Typs PersonWithActions, welche alle in der Datenbank gefundenen Daten enthält.
    """
    try:
        __check_for_initialization()
        sqlperson = "SELECT id, comment " \
                    "FROM Person " \
                    "WHERE name LIKE :name"

        if person_surname != '':
            sqlperson = sqlperson + " AND surname LIKE :surname"
            param = {'name': '%'+person_name+'%', 'surname': '%'+person_surname+'%'}
        else:
            param = {'name': '%' + person_name + '%'}

        connection, cursor = database_connect()
        cursor.execute(sqlperson, param)
        data_row = cursor.fetchone()
        if data_row is None:
            return DetailedPerson(None, 0, "", "", "")
        person_id = data_row[0]
        filenames = __get_pictures_by_personid(person_id)
        return DetailedPerson(filenames, person_id, person_name, person_surname, data_row[1])
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
        sql = "SELECT Picture.data, Person.name " \
              "FROM Picture " \
              "INNER JOIN Person ON Picture.personid = Person.id " \
              "WHERE Picture.personid = :id"
        param = {'id': person_id}

        connection, cursor = database_connect()
        cursor.execute(sql, param)
        data_rows = cursor.fetchall()
        fnames = []
        i = 1
        for data_row in data_rows:
            filename = data_row[1] + str(i) + '.jpg'
            fnames.append(filename)
            with open(tmp_directory + filename, 'wb') as output_file:
                output_file.write(data_row[0])
            i = i+1
        return fnames
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


def __get_personid_by_name(person_name, person_surname=''):
    """
    Sucht in der Datenbank nach einem Eintrag mit Übereinstimmung mit den Parametern. Wird ein Eintrag gefunden,
    so wird die ID des Eintrags zurückgegeben.
    :param person_name: Vorname der Person
    :param person_surname: Nachname der Person. Default=''
    :return: Person ID aus der Datenbank
    """
    try:
        __check_for_initialization()
        sql = "SELECT id " \
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


def get_all_pictures():
    """
    Erstellt für jeden in der Picture Tabelle der Datenbank vorhandenen Eintrag eine jpg Datei und schreibt die
    Daten in diese hinein.
    :return: Liste der Pfade zu den erstellten Dateien
    """
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
                i = 1
            filename = person + '.' + str(i) + '.jpg'
            i = i + 1
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


# region Delete-functions
def delete_person_by_name(person_name, person_surname=''):
    """
    Löscht einen Eintrag in der Person Tabelle anhand der Parameter person_name und person_surname.
    Dabei werden auch alle Referenzen auf diesen Eintrag aus Picture und PersonAction gelöscht.
    :param person_name: Vorname der Person
    :param person_surname: Nachname der Person. Default =''
    """
    try:
        __check_for_initialization()
        sql = "DELETE " \
              "FROM Person " \
              "WHERE id=:person_id"
        person_id = __get_personid_by_name(person_name, person_surname)
        param = {'person_id': person_id}
        connection, cursor = database_connect()
        __delete_images_by_personid(person_id, cursor)
        cursor.execute(sql, param)
        connection.commit()
        return person_id
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

        sql_del_pic = "DELETE " \
                      "FROM Picture " \
                      "WHERE personid=:person_id"
        param = {'person_id': person_id}
        connection, cursor = database_connect()
        cursor.execute(sql_del_pic, param)
        connection.commit()
        return cursor.rowcount
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
    :param cur: Cursor-Objekt, mit welchem die SQL-Anweisung ausgeführt werden soll
    """
    try:
        __check_for_initialization()

        sql_del_pic = "DELETE " \
                      "FROM Picture " \
                      "WHERE personid=:person_id"
        param = {'person_id': person_id}
        cur.execute(sql_del_pic, param)

        return cur.rowcount
    except Exception as e:
        raise e


# endregion


# region Insert-functions
def insert_person(person_name, person_surname='', comment=''):
    """
    Legt eine neue Person mit den notwendigen Daten in der Datenbank an.
    Ist durch eine Transaktion gesichert. Ist der Name bereits in der Datenbank vorhanden,
    so wird eine Exception geworfen.
    :param person_name: Name der Person
    :param person_surname: Nachname der Person. Default=''
    :param comment: Kommentar zum Eintrag. Default=''
    :return: ID des angelegten Eintrags zur Person
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        sql = "SELECT COUNT(*)" \
              "FROM Person " \
              "WHERE name LIKE :person_name"
        insert_sql = "INSERT INTO Person(name, surname, comment) VALUES(?,?,?)"

        if person_surname != '':
            sql = sql + " AND surname LIKE :person_surname"
            param = {'person_name': '%' + person_name + '%', 'person_surname': '%' + person_surname + '%'}
        else:
            param = {'person_name': '%' + person_name + '%'}

        # Execute the select query and check how many lines were affected
        cur.execute(sql, param)
        if cur.fetchone()[0] == 0:
            # If no lines were affected, the insert query is being executed and commited
            cur.execute(insert_sql, [person_name, person_surname, comment])
            con.commit()
        else:
            raise ValueError(person_name + " already exists in the specified database")
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e


def insert_picture(personid, file):
    """
    Erstellt einen Eintrag in der Picture Tabelle mir der in den Parametern gelieferten ID für eine Zuordnung zur
    Person Tabelle
    Ist durch eine Transaktion gesichert.
    :param personid: ID des Personeneintrags
    :param file: Pfad zu der zu speichernden Datei
    :return: ID des angelegten Eintrags in der Picture Tabelle
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()

        insert_sql = "INSERT INTO Picture(personid,data,filename) VALUES(?,?,?)"

        with open(file, 'rb') as input_file:
            # Open the file and save the data into ablob variable
            # ext defines the extension of the file (typically the structure ".jpg")
            # afile contains the pure filename, without file extension
            ablob = input_file.read()
            base = os.path.basename(file)
            afile, ext = os.path.splitext(base)
            cur.execute(insert_sql, [personid, sqlite3.Binary(ablob), afile])

        con.commit()
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e


def __insert_picture(personid, file, cur):
    """
    Erstellt einen Eintrag in der Picture Tabelle mir der in den Parametern gelieferten ID für eine Zuordnung zur
    Person Tabelle.
    :param personid: ID des Personeneintrags
    :param file: Pfad zu der zu speichernden Datei
    :param cur: Cursor-Objekt, mit welchem die SQL-Anweisung ausgeführt werden soll
    :return: ID des angelegten Eintrags in der Picture Tabelle
    """
    try:
        __check_for_initialization()

        insert_sql = "INSERT INTO Picture(personid,data,filename) VALUES(?,?,?)"

        with open(file, 'rb') as input_file:
            # Open the file and save the data into ablob variable
            # ext defines the extension of the file (typically the structure ".jpg")
            # afile contains the pure filename, without file extension
            ablob = input_file.read()
            base = os.path.basename(file)
            afile, ext = os.path.splitext(base)
            cur.execute(insert_sql, [personid, sqlite3.Binary(ablob), afile])

        return cur.lastrowid
    except Exception as e:
        raise e


def insert_picture_as_bytes(personid, byteobject):
    """
    Erstellt einen Eintrag in der Picture Tabelle mir der in den Parametern gelieferten ID für eine Zuordnung zur
    Person Tabelle.
    :param personid: ID des Personeneintrags
    :param byteobject: Rohe Byte-Daten der zu speichernden Datei
    :return: ID des angelegten Eintrags in der Picture Tabelle
    """
    try:
        __check_for_initialization()
        con, cur = database_connect()
        insert_sql = "INSERT INTO Picture(personid,data) VALUES(?,?)"

        cur.execute(insert_sql, [personid, sqlite3.Binary(byteobject)])

        con.commit()
        return cur.lastrowid
    except Exception as e:
        con.rollback()
        raise e
# endregion


# region Update-functions
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

        # Check if person with name already exists
        p = get_by_person(person_name, person_surname)
        if p.id != 0:
            raise Exception("Änderung nicht möglich. Es existiert bereits ein Eintrag mit demselben Namen.")

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

        cur.execute(sql, params)
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        raise e
# endregion

# region Classes


class Person:

    def __init__(self, id, name, surname, comment):
        self.id = id
        self.name = name
        self.surname = surname
        self.comment = comment


class DetailedPerson(Person):

    def __init__(self, filenames, id, name, surname, comment):
        Person.__init__(self, id, name, surname, comment)
        self.filenames = filenames

# endregion
