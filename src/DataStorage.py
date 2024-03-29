import datetime
from src import DataPersistence
from threading import RLock
import copy
import os
from contextlib import contextmanager
from scripts import interfacedb
import base64
USER = "user"
PASSWORD = "geheim"
THUMBNAIL_PATH = "data/recordings/thumbnails/"
RECORDINGS_PATH = "data/recordings/"
DATABASE_PATH = "./data/database/semesterprojekt.db"
TEMPORARY_PATH = "./Testbilder/test"

class PipcoDaten:
    __m_instance = None
    m_lock = None

    def __init__(self):
        if self.__m_instance is not None:
            raise Exception("Error - Trying to init second instance")
        else:
            self.m_data_persistence = DataPersistence.DataPersistence(self)
            self.__m_emails_lock = RLock()
            self.__m_log_lock = RLock()
            self.__m_log_fr_lock = RLock()
            self.__m_database_lock = RLock()
            self.__m_setting_lock = RLock()
            self.__m_settings = self.m_data_persistence.load_settings()
            self.__m_emails = self.m_data_persistence.load_emails()
            self.__m_log = self.m_data_persistence.load_logs()
            self.__m_log_fr = self.m_data_persistence.load_logs_fr()
            if not self.__m_log_fr:
                self.__m_log_fr = AutoIdDict()
            if not self.__m_log:
                self.__m_log = AutoIdDict()
            if not self.__m_emails:
                self.__m_emails = AutoIdDict()
            if not self.__m_settings:
                self.__m_settings = Settings()
            self.__m_instance = self
            self.__m_image = None
            self.__m_image_fr = None
            self.__m_image_without = None
            self.__m_user = USER
            self.__m_password = PASSWORD
            interfacedb.initialize(DATABASE_PATH, TEMPORARY_PATH)
            self.m_stream_fps = 30
            self.m_data_persistence.save_settings(self.__m_settings)

    @staticmethod
    def get_instance():
        if PipcoDaten.__m_instance is None:
            PipcoDaten.__m_instance = PipcoDaten()
        return PipcoDaten.__m_instance

    @contextmanager
    def lock_all(self):
        self.__m_log_lock.acquire()
        self.__m_emails_lock.acquire()
        self.__m_setting_lock.acquire()
        try:
            yield self.__m_log_lock and self.__m_emails_lock and self.__m_setting_lock
        finally:
            self.__m_log_lock.release()
            self.__m_emails_lock.release()
            self.__m_setting_lock.release()

    def toggle_mail_notify(self, id):
        with self.__m_emails_lock:
            state = not self.__m_emails[int(id)].notify
            self.__m_emails[int(id)].notify = state
            self.m_data_persistence.save_emails(self.__m_emails)
            return state

    def add_mail(self, address):
        with self.__m_emails_lock:
            ret = self.__m_emails.append(Mail(address))
            self.m_data_persistence.save_emails(self.__m_emails)
            return ret

    def create_person(self, person):
        name = person.get('name')
        surname = person.get('surname')
        comment = person.get('comment')
        file = person.get('file')

        missing_padding = len(file) % 4
        while missing_padding:
            file += '='
            missing_padding = len(file) % 4

        file = base64.b64decode(file.replace('data:image/jpeg;base64,', '', 1))


        with self.__m_database_lock:
            ret = interfacedb.insert_person(name, surname, comment)
            ret_file = interfacedb.insert_picture_as_bytes(ret, file)

            return ret

    def remove_mail(self, id):
        with self.__m_emails_lock:
            self.__m_emails.__delitem__(id)
            self.m_data_persistence.save_emails(self.__m_emails)
            return id

    def get_mails(self):
        with self.__m_emails_lock:
            ret = copy.deepcopy(self.__m_emails)
            return ret

    def get_settings(self):
        with self.__m_setting_lock:
            ret = copy.copy(self.__m_settings)
            return ret

    def change_settings(self, sensitivity=None, brightness=None, contrast=None, streamaddress=None, global_notify=None,
                        log_enabled=None, fr_log_enabled=None, cliplength=None, max_logs=None, max_storage=None,
                        cam_mode=None):
        with self.__m_setting_lock:
            ret = {}
            if sensitivity is not None:
                ret["sensitivity"] = sensitivity
                self.__m_settings.sensitivity = float(sensitivity)
            if brightness is not None:
                ret["brightness"] = brightness
                self.__m_settings.brightness = float(brightness)
            if contrast is not None:
                ret["contrast"] = contrast
                self.__m_settings.contrast = float(contrast)
            if streamaddress is not None:
                ret["streamaddress"] = streamaddress
                self.__m_settings.streamaddress = streamaddress
            if global_notify is not None:
                ret["global_notify"] = global_notify
                self.__m_settings.global_notify = bool(global_notify)
            if log_enabled is not None:
                ret["log_enabled"] = log_enabled
                self.__m_settings.log_enabled = bool(log_enabled)
            if fr_log_enabled is not None:
                ret["fr_log_enabled"] = fr_log_enabled
                self.__m_settings.fr_log_enabled = bool(fr_log_enabled)
            if cliplength is not None:
                ret["cliplength"] = cliplength
                self.__m_settings.cliplength = int(cliplength)
            if max_logs is not None:
                ret["max_logs"] = max_logs
                self.__m_settings.max_logs = int(max_logs)
            if max_storage is not None:
                ret["max_storage"] = max_storage
                self.__m_settings.max_storage = int(max_storage)
            if cam_mode is not None:
                ret["cam_mode"] = cam_mode
                self.__m_settings.cam_mode = int(cam_mode)
            self.m_data_persistence.save_settings(self.__m_settings)
            return ret

    def set_image(self, image):
        self.__m_image = image

    def get_image(self):
        return self.__m_image

    #Images für Facerecognition-Stream
    def set_image_fr(self, image):
        self.__m_image_fr = image

    def get_image_fr(self):
        return self.__m_image_fr

    #Images für Stream ohne Facerecognition oder Movement-Detection
    def set_image_without(self, image):
        self.__m_image_without = image

    def get_image_without(self):
        return self.__m_image_without

    def get_log_page(self, page, batchsize):
        with self.__m_log_lock:
            selected = {}
            for idx, key in enumerate(sorted(self.__m_log.keys(), reverse=True)[int(page)*int(batchsize):]):
                selected[key] = copy.copy(self.__m_log[key])
                if int(batchsize)-1 == idx:
                    return selected
            return selected

    def get_log_page_fr(self, page, batchsize):
        with self.__m_log_lock:
            selected = {}
            for idx, key in enumerate(sorted(self.__m_log_fr.keys(), reverse=True)[int(page)*int(batchsize):]):
                selected[key] = copy.copy(self.__m_log_fr[key])
                if int(batchsize)-1 == idx:
                    return selected
            return selected

    def get_free_index(self):
        with self.__m_log_lock:
            return self.__m_log.get_free_index()
    def get_free_index_fr(self):
        with self.__m_log_fr_lock:
            return self.__m_log_fr.get_free_index()

    def add_log(self):
        max_logs = self.get_settings().max_logs
        with self.__m_log_lock:
            if len(self.__m_log) >= max_logs:
                idx = self.__m_log.get_oldest_key()
                self.remove_log(idx)
            idx = self.__m_log.get_free_index()
            idx = self.__m_log.append(Log(idx))
            self.m_data_persistence.save_logs(self.__m_log)
            return idx

    def add_log_fr(self):
        max_logs = self.get_settings().max_logs
        with self.__m_log_fr_lock:
            if len(self.__m_log_fr) >= max_logs:
                idx = self.__m_log_fr.get_oldest_key()
                self.remove_log_fr(idx)
            idx = self.__m_log_fr.get_free_index()
            idx = self.__m_log_fr.append(Log(idx))
            self.m_data_persistence.save_logs_fr(self.__m_log_fr)
            return idx

    def check_login(self, user, password):
        return self.__m_user == user and self.__m_password == password

    def remove_log(self, id):
        from src.ImageProcessing import THUMBNAIL_TYPE, RECORDING_TYPE
        with self.__m_log_lock:
            try:
                os.remove(THUMBNAIL_PATH + str(id) + THUMBNAIL_TYPE)
            except FileNotFoundError as e:
                print(e)
            try:
                os.remove(RECORDINGS_PATH + str(id) + RECORDING_TYPE)
            except FileNotFoundError as e:
                print(e)
            self.__m_log.__delitem__(id)
            self.m_data_persistence.save_logs(self.__m_log)
        return id

    def remove_log_fr(self, id):

        from src.Gesichtsreidentifikation import Gesichtsreidentifikation
        with self.__m_log_lock:
            try:
                os.remove('data/videos/' + 'thumbnails/' + str(id) + '.jpg')
            except FileNotFoundError as e:
                print(e)
            try:
                os.remove('data/videos/' + str(id) + '.mp4')
            except FileNotFoundError as e:
                print(e)
            self.__m_log_fr.__delitem__(id)
            self.m_data_persistence.save_logs_fr(self.__m_log_fr)
        return id


class AutoIdDict(dict):
    """Dictionary with auto increment id as key"""
    def __init__(self, list=None):
        if list:
            for val in list:
                self[val.id] = val
        super(dict, self).__init__()

    def append(self, val):
        if val in self.values():
            return -1
        index = self.get_free_index()
        val.id = index
        self[index] = val
        return index

    def get_free_index(self):
        if self:
            ret = sorted(self.keys())[-1]+1
            return ret
        else:
            return 0

    def get_oldest_key(self):
        if self.keys():
            idx = sorted(self.keys())[0]
            return idx

class Mail:
    def __init__(self, address, id=0, notify=True):
        self.address = address
        self.notify = notify
        self.id = id

    def __eq__(self, other):
        return self.address == other.address

class Person:
    def __init__(self, name, role, surname='', comment='', files=None):
        self.name = name
        self.surname = surname
        self.role = role
        self.comment = comment
        self.files = files


class Log:
    def __init__(self, id=0, timestamp=None, message=""):
        if not timestamp:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.message = message
        self.timestamp = timestamp
        self.id = id


class Settings:
    def __init__(self, sensitivity=0.0, brightness=0.0, contrast=0.5, streamaddress="", global_notify=True,
                 log_enabled=True, fr_log_enabled=True, cliplength=30, max_logs=5, max_storage=2048,
                 cam_mode=0):
        self.sensitivity = sensitivity
        self.streamaddress = streamaddress
        self.brightness = brightness
        self.contrast = contrast
        self.global_notify = global_notify
        self.log_enabled = log_enabled
        self.cliplength = cliplength
        self.max_logs = max_logs
        self.max_storage = max_storage
        self.cam_mode = cam_mode
        self.fr_log_enabled = fr_log_enabled
