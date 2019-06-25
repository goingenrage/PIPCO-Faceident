import unittest
from scripts import interfacedb as interface
import random
import os

db_location = "/home/michael/PycharmProjects/gesichtserkennung/data/database/db.sql"
tmp_location = "/home/michael/tmp/"
gallery = "/home/michael/PycharmProjects/gesichtserkennung/Testbilder/test/"


class TestMiscellaneousMethods(unittest.TestCase):

    def test_Initialization(self):
        self.assertTrue(interface.initialize(db_location, tmp_location))
        self.assertTrue(interface.check_for_initialization())

    def test_ExceptionInitialization(self):
        self.assertTrue(interface.initialize("", ""))
        with self.assertRaises(Exception):
            interface.check_for_initialization()

    def test_DumpDatabase(self):
        dumpname = interface.database_dump(tmp_location)
        self.assertNotEqual("", dumpname)
        os.remove(dumpname)


    # def test_ImportDatabase(self):
    #     self.assertTrue(interface.database_import(tmp_location + "25_06_2019_10_59_50_dump.sql"))


class TestInsertMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_ExceptionPersonInsert(self):
        with self.assertRaises(ValueError):
            interface.insert_person("testname")

    def test_PersonInsertAndDelete(self):
        self.assertTrue(interface.insert_person("Second", "Person", "With Comment"))
        self.assertEqual(interface.get_by_person("Second").id, interface.delete_person_by_name("Second"))

    def test_PersonInsert(self):
        random_num = random.randint(1, 50000)
        self.assertTrue(interface.insert_person("Insert"+str(random_num), "Person", "With Comment"))
        self.assertLess(0, interface.delete_person_by_name("Insert"+str(random_num)))

    def test_PictureInsertFile(self):
        self.assertLess(0, interface.insert_picture(7, gallery+"valentin.1.jpg"))
        self.assertEqual(1, interface.delete_images_by_personid(7))

    def test_ExceptionPictureNotFound(self):
        with self.assertRaises(FileNotFoundError):
            interface.insert_picture(7, "abcdefgh")

    def test_PictureInsertBytes(self):
        with open(gallery+"valentin.1.jpg", 'rb') as input_file:
            ablob = input_file.read()
        self.assertLess(0, interface.insert_picture_as_bytes(7, ablob))
        self.assertEqual(1, interface.delete_images_by_personid(7))


class TestUpdateMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_PersonUpdate(self):
        self.assertTrue(interface.update_person(10, "zehn"))
        self.assertEqual(10, interface.get_by_person("zehn").id)
        self.assertTrue(interface.update_person(10, "b4Update"))

    def test_ExceptionPersonUpdate(self):
        with self.assertRaises(Exception):
            interface.update_person(9, "this")


class TestDeleteMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_PersonDelete(self):
        interface.insert_person("test for Deleting")
        self.assertLess(0, interface.delete_person_by_name("test for Deleting"))

    def test_PictureDelete(self):
        interface.insert_picture(10, gallery+"valentin.3.jpg")
        self.assertEqual(1, interface.delete_images_by_personid(10))

    def test_PictureDeleteNone(self):
        self.assertEqual(0, interface.delete_images_by_personid(9))


class TestReadingMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_GetPerson(self):
        self.assertEqual(1, interface.get_by_person("testname").id)

    def test_GetNonExistingPerson(self):
        self.assertEqual(0, interface.get_by_person("Barack").id)

    def test_GetAllPersons(self):
        self.assertEqual(len(interface.get_all_persons()), 46)

    def test_GetAllPictures(self):
        self.assertEqual(len(interface.get_all_pictures()), 3)


if __name__ == '__main__':
    unittest.main()
