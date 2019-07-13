# Dokumentation und Beschreibung der Testfaelle ist in der Projektdokumentation zu finden.


import unittest
from scripts import interfacedb as interface
import random
import os

db_location = "../scripts/dbunittest/unittest.db"
tmp_location = "../scripts/dbunittest/tmp/"
gallery = "../scripts/dbunittest/testgallery/"


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
        self.assertLess(0, interface.insert_picture(3, gallery+"testbild.jpg"))
        self.assertEqual(1, interface.delete_images_by_personid(3))

    def test_ExceptionPictureNotFound(self):
        with self.assertRaises(FileNotFoundError):
            interface.insert_picture(1, gallery+"abcdefgh")

    def test_PictureInsertBytes(self):
        with open(gallery+"testbild.jpg", 'rb') as input_file:
            ablob = input_file.read()
        self.assertLess(0, interface.insert_picture_as_bytes(1, ablob))
        self.assertEqual(1, interface.delete_images_by_personid(1))


class TestUpdateMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_PersonUpdate(self):
        self.assertTrue(interface.update_person(2, "zwei"))
        self.assertEqual(2, interface.get_by_person("zwei").id)
        self.assertTrue(interface.update_person(2, "b4Update"))

    def test_ExceptionPersonUpdate(self):
        with self.assertRaises(Exception):
            interface.update_person(3, "testname")


class TestDeleteMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_PersonDelete(self):
        interface.insert_person("test for Deleting", "should be deleted by unittests")
        self.assertLess(0, interface.delete_person_by_name("test for Deleting"))

    def test_PictureDelete(self):
        interface.insert_picture(2, gallery+"testbild.jpg")
        self.assertEqual(1, interface.delete_images_by_personid(2))

    def test_PictureDeleteNone(self):
        self.assertEqual(0, interface.delete_images_by_personid(3))


class TestReadingMethods(unittest.TestCase):

    def setUp(self):
        interface.initialize(db_location, tmp_location)

    def test_GetPerson(self):
        self.assertEqual(1, interface.get_by_person("testname").id)

    def test_GetNonExistingPerson(self):
        self.assertEqual(0, interface.get_by_person("Barack").id)

    def test_GetAllPersons(self):
        self.assertEqual(len(interface.get_all_persons()), 3)

    def test_GetAllPictures(self):
        self.assertEqual(len(interface.get_all_pictures()), 0)


if __name__ == '__main__':
    unittest.main()
