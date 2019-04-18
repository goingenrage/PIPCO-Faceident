import os
import sqlite3
from time import sleep

from PIL import Image

db_directory = '/home/michael/semesterprojekt.db'
tmp_directory = '/home/michael/tmp/'


#   Database connection function
#   Returns a connection and a cursor object
def new_database(name):
    con = sqlite3.connect(name)
    cur = con.cursor()
    return con, cur

#   Retrieve all images to a given person_name out of the database
#   Images are saved into a directory, defined as tmp_directory, in order to access them
def extract_picture(cursor, person_name):
    sql = "SELECT Picture.data, Picture.type, Picture.filename " \
          "FROM Picture " \
          "INNER JOIN PersonPicture ON Picture.id = PersonPicture.pictureid " \
          "INNER JOIN Person ON PersonPicture.personid = Person.id " \
          "WHERE Person.name like :name"
    param = {'name': '%'+person_name+'%'}

    cursor.execute(sql, param)
    fnames = []
    rows = cursor.fetchall()

    for row in rows:
        #   row[0] contains image data
        #   row[1] contains file extension
        #   row[2] contains filename
        filename = row[2] + row[1]
        fnames.append(filename)
        with open(tmp_directory + filename, 'wb') as output_file:
            output_file.write(row[0])
    return fnames


if __name__ == "__main__":
    try:
        con, cur = new_database(db_directory)
        filenames = extract_picture(cur, "martin")
        for filename in filenames:
            image = Image.open(tmp_directory + '/' + filename);
            image.show()
            sleep(3)

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
            except Exception as e:
                print(e)
