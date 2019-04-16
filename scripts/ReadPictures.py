import os
import sqlite3
from time import sleep

from PIL import Image

db_directory = '/home/michael/semesterprojekt.db'
tmp_directory = '/home/michael/tmp/'


def new_database(name):
    con = sqlite3.connect(name)
    cur = con.cursor()
    return con, cur


def extract_picture(cursor, person_name):
    sql = "SELECT Picture.data, Picture.type, Picture.filename " \
          "FROM Picture " \
          "INNER JOIN PersonPicture ON Picture.id = PersonPicture.pictureid " \
          "INNER JOIN Person ON PersonPicture.personid = Person.id " \
          "WHERE Person.name like :name"
    sql2 = "SELECT Picture.data, Picture.type, Picture.filename " \
           "FROM Picture " \
           "WHERE id=:id"
    param = {'name': '%martin%'}
    param2 = {'id': '9'}

    cursor.execute(sql, param)
    ablobs = []
    exts = []
    afiles = []
    fnames = []
    rows = cursor.fetchall()
    for row in rows:
        ablobs.append(row[0])
        exts.append(row[1])
        afiles.append(row[2])
    for index, ext in enumerate(exts):
        filename = afiles[index] + ext
        fnames.append(filename)
        with open(tmp_directory + filename, 'wb') as output_file:
            output_file.write(ablobs[index])
    return fnames


if __name__ == "__main__":
    try:
        con, cur = new_database(db_directory)
        filenames = extract_picture(cur, "martin.7")
        for filename in filenames:
            image = Image.open(tmp_directory + '/' + filename);
            image.show()
            sleep(3)
        # image = Image.open('/home/michael/PycharmProjects/master/test123123.jpg')
    except Exception as e:
        print(e)
    finally:
        # Clean the tmp directory
        folder = '/home/michael/tmp'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)
