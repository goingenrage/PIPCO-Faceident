from scipy.spatial import distance
import os
import cv2

import json
from openvino.inference_engine import IENetwork, IEPlugin
from pathlib import Path
import time
from threading import Thread
from src import create_list
import configparser
from src.DataStorage import *
import logging
import platform
from src.MailClient import MailClient


from scripts import interfacedb



CODECS = {"Linux": "avc1", "Darwin": "avc1", "Windows": "AVC1"}

class Gesichtsreidentifikation(Thread):

# region Global variables
    __model_xml = ""
    __model_bin = ""
    __model_reid_xml = ""
    __model_reid_bin = ""
    __path_to_database = ""
    __path_to_tmpfolder = ""
    __path_to_cpuextension = ""
    __path_to_outputvid = ""

    __globalReIdVec = []
    __unknownPersons = []
    __unknownRecentlySeen = {}
    __names = {}
    __face_gallery = ""
    __frame_list = []
    __recentlySeen = {}
    __model_n = 0
    __model_c = 0
    __model_h = 0
    __model_w = 0
    __model_reid_n = 0
    __model_reid_c = 0
    __model_reid_h = 0
    __model_reid_w = 0
    __input_blob_reid = []
    __out_blob_reid = []
    __input_blob = []
    __out_blob = []
    __exec_net = []
    __exec_net_reid = []
    __cap = None
    __config_path = ""
    __path_to_camera = ""
#endregion

    def __init__(self, config_path):
        """
        Wird beim starten des Threads aufgerufen. Initialisiert alle benötigten Module.
        :param config_path: Pfad zum Config-File welches die Konfiguration für den Programmstart beinhaltet.
        """
        self.__config_path = config_path
        self.__data = PipcoDaten.get_instance()
        self.__settings = self.__data.get_settings()
        self.__mailing = MailClient(self.__data)
        super(Gesichtsreidentifikation, self).__init__()


    def __init_variables(self):
        """
        Hier werden alle Variablen initialisiert, welche durch das Config-File gesteuert werden.
        """
        config = configparser.RawConfigParser()
        config.read(self.__config_path)

        self.__face_gallery = config.get('DEFAULT', 'face_gallery')
        self.__model_xml = config.get('DEFAULT', 'model_xml')

        self.__model_bin = config.get('DEFAULT', 'model_bin')


        self.__model_reid_xml = config.get('DEFAULT', 'model_reid_xml')

        self.__model_reid_bin = config.get('DEFAULT', 'model_reid_bin')


        self.__path_to_database = config.get('DEFAULT', 'path_to_database')

        self.__path_to_tmpfolder = config.get('DEFAULT', 'path_to_tmpfolder')

        self.__path_to_camera = config.get('DEFAULT', 'path_to_camera')
        self.__path_to_cpuextension = config.get('DEFAULT', 'path_to_cpuextension')
        self.__path_to_outputvid = config.get('DEFAULT', 'path_to_outputvid')


    def __clearDirectory(self):
        """
        Hier wird das Verzeichnis geleert, bevor aus der Datenbank alle Referenzbilder reingelegt werden.
        """
        folder = self.__path_to_tmpfolder
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)


    def __getImagesFromDatabase(self):
        """
        Es werden alle Referenzbilder aus der Datenbank geholt und in das Verzeichnis gespeichert, welches in dem
        Config-File angegeben wurde.
        """
        print("Hole Bilder aus Datenbank")

        self.__clearDirectory()
        interfacedb.initialize(self.__path_to_database, self.__path_to_tmpfolder)
        interfacedb.database_connect()
        interfacedb.get_all_pictures()

        ##create_list.create_list(self.path_to_tmpfolder)


    def __personGallery(self):
        """
        Hier werden die Referenzbilder aus der Datenbank geholt und anschließend durch die Inference Engine geschoben.
        Dadurch wird die Matrize für jedes Referenzbild erstellt um diese später für die Wiedererkennung zu nutzen.
        """
        self.__getImagesFromDatabase()
        create_list.create_list(self.__path_to_tmpfolder) # Aufruf um ein json file zu generieren welches Angaben zu
                                                          # Pfadnahmen und Namen der Person beinhaltet.
        with open(self.__face_gallery, "r") as read_file:
            faces = json.load(read_file)
        print(self.__face_gallery)

        id = 0
        # print(faces)
        for face in faces: # Alle Personen die in dem json-File stehen werden durchgegangen
            print(face)
            label = face
            for path in faces[face]: # Jedes Bild der Person wird eingelesen.
                config = Path(path)
                if not config.is_file(): # Falls Pfadangabe fehlerhaft ist soll dieser Pfad geskippt werden.
                    break

                image = cv2.imread(path)
                reId = self.__create_reference_matrix(image) # Aufruf um die Matrize des Bildes zu bekommen.
                self.__globalReIdVec.append(reId) # Hier werden alle Matrizen für den späteren Vergleich gespeichert.
                self.__names[id] = label # Namen werden unter der Nummer der  Matrize gespeihert, um später einen Namen
                                        # zuordnen zu können.
                id += 1


    def __initReidentification(self):
        """
        Initialisierung aller Variablen, die für die Gesichtsreidentifikation benötigt werden. Vorallem wird hier die
        Inference Engine von OpenVINO initialisiert.
        """
        if self.__path_to_camera == '0':
            self.__cap = cv2.VideoCapture(0)
        else:
            self.__cap = cv2.VideoCapture(self.__path_to_camera)
        net = IENetwork(model=self.__model_xml, weights=self.__model_bin)
        net_reid = IENetwork(model=self.__model_reid_xml, weights=self.__model_reid_bin)

        plugin = IEPlugin(device="CPU")
        plugin.add_cpu_extension(self.__path_to_cpuextension)
        plugin_reid = IEPlugin(device="CPU")
        plugin_reid.add_cpu_extension(self.__path_to_cpuextension)
        # plugin_reid.set_config(net_reid)
        self.__exec_net = plugin.load(network=net, num_requests=1)
        self.__exec_net_reid = plugin_reid.load(network=net_reid, num_requests=1)

        self.__input_blob = next(iter(net.inputs))
        self.__out_blob = next(iter(net.outputs))
        # print('network.inputs = ' + str(list(net.inputs)))
        # print('network.outputs = ' + str(list(net.outputs)))
        self.__model_n, self.__model_c, self.__model_h, self.__model_w = net.inputs[self.__input_blob].shape

        self.__input_blob_reid = next(iter(net_reid.inputs))
        self.__out_blob_reid = next(iter(net_reid.outputs))

        self.__model_reid_n, self.__model_reid_c, self.__model_reid_h, self.__model_reid_w = net_reid.inputs[self.__input_blob_reid].shape

        # print('network.inputs = ' + str(list(net_reid.inputs)))
        # print('network.outputs = ' + str(list(net_reid.outputs)))


    def __create_reference_matrix(self,image):
        """
        Hier wird über die Inference Engine eine Matrize des übergebenen Bildes erstellt, welche dann später für die
        Wiedererkennung dieser Person genutzt wird.
        :param image: Bild der Person welche später wiedererkannt werden soll.
        :return reIdVector: Matrize der Person welche per Bild übergeben wurde.
        """
        cap_h, cap_w, _ = image.shape # Speichert die Größe des Bildes
        #im = cv2.resize(image, (640, 480)) # Resize, um alle Bilder auf der selben Größe zu haben.

        in_frame = cv2.resize(image, (self.__model_w, self.__model_h))
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape((self.__model_n, self.__model_c, self.__model_h, self.__model_w))

        self.__exec_net.start_async(request_id=0, inputs={self.__input_blob: in_frame}) # Das eingegebene Bild wird auf
                                                                                        # Gesichter durchsucht.
        try:
            if self.__exec_net.requests[0].wait(-1) == 0: # Wenn die Inference Engine fertig mit suchen von Gesichtern ist
                res = self.__exec_net.requests[0].outputs[self.__out_blob]
                for obj in res[0][0]: # Für alle Gesichter, die in dem übergebenen Bild entdeckt wurden.
                    class_id = int(obj[1])
                    if class_id == 1:
                        if obj[2] > 0.5:
                            xmin = int(obj[3] * cap_w)
                            ymin = int(obj[4] * cap_h)
                            xmax = int(obj[5] * cap_w)
                            ymax = int(obj[6] * cap_h)
                            frame_org = image.copy()
                            person = frame_org[ymin:ymax, xmin:xmax] # Hier wird das eingegebene Bild genau auf das
                                                                    # Gesicht der Person zugeschnitten
                            in_frame_reid = cv2.resize(person, (self.__model_reid_w, self.__model_reid_h))
                            in_frame_reid = in_frame_reid.transpose((2, 0, 1))
                            in_frame_reid = in_frame_reid.reshape((self.__model_reid_n, self.__model_reid_c, self.__model_reid_h, self.__model_reid_w))
                            # Das Gesicht wird auf seine eindeutigen Merkmale durchsucht
                            self.__exec_net_reid.start_async(request_id=0, inputs={self.__input_blob_reid: in_frame_reid})

                            if self.__exec_net_reid.requests[0].wait(-1) == 0:
                                res_reid = self.__exec_net_reid.requests[0].outputs[self.__out_blob_reid]
                                reIdVector = res_reid[0].reshape(-1, )

                                return reIdVector
        except Exception as e:
            print("exception: " + str(e))
        return None


    def createMatchingPerson(self, newReIdVec):

        size = len(self.__globalReIdVec)

        self.__globalReIdVec.append(newReIdVec)
        return len(self.__globalReIdVec) - 1


    def __findMatchingPerson(self, newReIdVec):
        """
        Sucht mithilfe der Kosinusähnlichkeit eine Matrize aus den Referenzmatrizen, welche mit der
        übergebenen sehr ähnlich ist.
        :param newReIdVec: Matrize, zu der eine bekannte Person gesucht werden soll.
        :return idx: Index der Person, zu der die übergebene Matrize passt. Falls keine gefunden wurde -1
        """
        size = len(self.__globalReIdVec)
        idx = size
        for i in range(size):

            cosSim = self.__cosineSimilarity(newReIdVec, self.__globalReIdVec[i])
            #print(cosSim)
            if cosSim > 0.5:
                # globalReIdVec[i] = newReIdVec.copy() #ist es sinnvoll bei einem erkannten gesicht den vector zu aktualisieren?
                # was passiert bei einer falschen erkennung?
                idx = i
                break

        if idx < size:
            return idx
        else:
            return -1


    def __cosineSimilarity(self, u,v):
        # Durch die Berechnung der Cosinus-Ähnlichkeit (siehe https://en.wikipedia.org/wiki/Cosine_similarity) wird verglichen,
        # ob die beiden Vectoren ähnlich sind.
        return float(1 - distance.cosine(u, v))

    def __isUnknown(self, reIdVec):
        """
        Prüft ob erkanntes, nicht reidentifizierbares Gescht schon einmal gesehen wurde.
        :param reIdVec: Matrize, mit der geprüft werden soll
        :return idx: Wenn Person schoneinmal gesehen wurde dessen Index, sonst -1
        :return unknown: Wenn Person schoneinmal gesehen wurde False, sonst True
        """
        size = len(self.__unknownPersons)
        for i in range(size):
           if self.__cosineSimilarity(reIdVec, self.__unknownPersons[i]) > 0.5:
               return i, False
        return -1, True

    def __save_thumbnail(self, image, id):
        """
        Speichert für eine aufgenommene Videosequenz ein Thumbnail ab.
        :param image: Das Bild, das als Thumbnail ausgewählt wurde.
        :param id: Die Id des Videos, zudem das Thumbnail gehört.
        """
        small = cv2.resize(image, (0, 0), fx=0.2, fy=0.2)
        cv2.imwrite(self.__path_to_outputvid + 'thumbnails/' + str(id) + '.jpg', small)

    def __storage_manager(self):
        """
        Prüft, ob noch freier Speicherplatz vorhanden ist, um Videos aufzuzeichnen. Wenn nicht, wird eine
        Email versendet, damit jemand freien Speicher schaffen kann. Wenn freier Speicher verfügbar ist, wird die
        Videosequenz in den FR-Log übernommen und dazu ein THumbnail gespeichert.
        :return:
        """
        from src.DataPersistence import DataPersistence
        self.__m_storage_full = int(DataPersistence.get_size_of_folder("data/") / 2 ** 20) >= self.__settings.max_storage
        if self.__m_storage_full:
            self.__mailing.notify_storage_full()
        else:
            idx = self.__data.add_log_fr()
            self.__save_thumbnail(self.__frame_list[int(len(self.__frame_list)/3)], idx)

    def run(self):
        """
        Main-Loop, alle Initialisierungsmethoden werden aufgerufen, Frames werden von der Kamera geholt und dann
        die Reidentifikation ausgeführt. Basierend auf dem Ergebnis der Reidentifikation wird entschieden, welche
        Schritte weiter durchgefphrt werden.
        """

        self.__init_variables()
        self.__initReidentification()
        self.__personGallery()
        update_timer = Timer(1)
        start_recording = False
        start_time = 0

        out = None
        #self.cap = cv2.VideoCapture("http://192.168.0.35/cgi-bin/videostream.cgi?user=admin&pwd=admin")
        print("init done")

        reallyUnknown = 0;
        while True:


            ret, frame = self.__cap.read() # Frame wird aus dem Kamerastream geholt
            if not ret:
                break
            ret2, jpg = cv2.imencode('.jpg', frame) # Frame wird für den Outputstream gespeichert, ohne dass das
                                                    # Frame verändert wurde
            self.__data.set_image_without(jpg)
            cap_w = self.__cap.get(3)
            cap_h = self.__cap.get(4)
            in_frame = cv2.resize(frame, (self.__model_w, self.__model_h))
            in_frame = in_frame.transpose((2, 0, 1))
            in_frame = in_frame.reshape((self.__model_n, self.__model_c, self.__model_h, self.__model_w))

            self.__exec_net.start_async(request_id=0, inputs={self.__input_blob: in_frame}) # Gesichtserkennung wird auf
                                                                                        # dem aktuellen Frame gestartet

            if self.__exec_net.requests[0].wait(-1) == 0:

                res = self.__exec_net.requests[0].outputs[self.__out_blob]

                for obj in res[0][0]: # Für alle erkannten Gesichter im aktuellen Frame
                    try:
                        class_id = int(obj[1])
                        if class_id == 1:
                            if obj[2] > 0.5:
                                xmin = int(obj[3] * cap_w)
                                ymin = int(obj[4] * cap_h)
                                xmax = int(obj[5] * cap_w)
                                ymax = int(obj[6] * cap_h)
                                frame_org = frame.copy()
                                person = frame_org[ymin:ymax, xmin:xmax] # Aus dem aktuellen Frame wird das erkannte
                                                                         # Gesicht rausgeschnitten
                                # Das ausgeschnittene Gesicht wird für die Reidentifizierung vorbereitet
                                in_frame_reid = cv2.resize(person, (self.__model_reid_w, self.__model_reid_h))
                                in_frame_reid = in_frame_reid.transpose((2, 0, 1))
                                in_frame_reid = in_frame_reid.reshape(
                                    (self.__model_reid_n, self.__model_reid_c, self.__model_reid_h, self.__model_reid_w))

                                # Das vorbereitete Gescht wird in die Reidentifizierung geschickt
                                self.__exec_net_reid.start_async(request_id=0, inputs={self.__input_blob_reid: in_frame_reid})

                                if self.__exec_net_reid.requests[0].wait(-1) == 0:
                                    res_reid = self.__exec_net_reid.requests[0].outputs[self.__out_blob_reid]
                                    reIdVector = res_reid[0].reshape(-1, )

                                    foundId = self.__findMatchingPerson(reIdVector) # Sucht zu der vorher ermittelten
                                                                                    # Matrize eine passende Person

                                    # Zeichnet um jedes erkannte Gesicht ein Rechteck auf das Frame
                                    color = (255, 0, 0)
                                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                                    idColor = (0, 0, 255)
                                    #print(foundId)
                                    if foundId is not -1: # Wenn eine Person wiedererkannt wurde
                                        cv2.putText(frame, self.__names[foundId], (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                    idColor,
                                                    1) # Schreibt den Namen der erkannten Person über das vorher gezeichnete Rechteck
                                        #Hier soll geprüft werden, wann die Person zuletzt gesehen wurde, um Aktionen nicht bei jedem Frame auszuführen.
                                        if not self.__recentlySeen.__contains__(self.__names[foundId]) or (time.time() - self.__recentlySeen[self.__names[foundId]]) > 10:
                                            print("Person " + self.__names[foundId] + " wurde erkannt!")
                                            logging.info("Person " + self.__names[foundId] + " wurde erkannt!")
                                            self.__recentlySeen[self.__names[foundId]] = time.time()



                                    else: # Wenn eine Person nicht wiedererkannt werden konnte
                                        reallyUnknown = reallyUnknown +1 # Zählt wieoft eine Person nicht wiedererkannt
                                                                        # werden konnte um falschmeldungen zu vermeiden
                                        unknownID,tmp = self.__isUnknown(reIdVector)
                                        if reallyUnknown > 10 and tmp:
                                            reallyUnknown = 0
                                            unallowed_person_in_room = True
                                            self.__unknownPersons.append(reIdVector)
                                            self.__unknownRecentlySeen[len(self.__unknownPersons)-1] = time.time()
                                            print("Unbekannte Person entdeckt!")
                                            self.__mailing.notify_unknown_person_detected()
                                            logging.warning("Unbekannte Person entdeckt!")
                                            cv2.putText(frame, "Unknown", (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                        idColor, 1)
                                        if tmp == False:
                                            reallyUnknown = 0
                                            if time.time() - self.__unknownRecentlySeen[unknownID] > 100:
                                                self.__unknownRecentlySeen[unknownID] = time.time()
                                                print("Unbefugte Person wurde zuvor erkannt")
                                                logging.warning("Unbefugte Person wurde zuvor erkannt")
                                            cv2.putText(frame, str(unknownID), (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                        idColor, 1)


                    except Exception as e:
                        print("exception in main" + str(e))

                # Wenn aktuell keine Videosequenz aufgezeichnet wird, und fr_log_enabled True ist, soll das aufzeichnen
                # von Videosequenzen initialisiert werden
                if not start_recording and self.__settings.fr_log_enabled:
                    print("Start recording...")
                    start_recording = True
                    start_time = time.time()

                    self.__m_frame_list = []
                    idx = self.__data.get_free_index_fr()
                    output_str = self.__path_to_outputvid + str(idx) + '.mp4'
                    print( cv2.VideoWriter_fourcc(*CODECS[platform.system()]))
                    out = cv2.VideoWriter(output_str,  cv2.VideoWriter_fourcc(*CODECS[platform.system()]), 10.0, (640, 480))

                if start_recording: # Wenn start_recording True ist, soll das aktuelle Frame in den Videostream
                                    # geschickt werden.
                    out.write(frame)
                    self.__frame_list.append(frame)
                    if time.time() - start_time > 50: # Wenn die Zeit für das Video um ist, wird die Aufzeichnung
                                                      # abgeschlossen und eine weitere kann beginnen.
                        start_recording = False
                        self.__storage_manager()
                        out.release()
                        print("Recording end...")
            ret2, jpg = cv2.imencode('.jpg', frame)
            self.__data.set_image_fr(jpg)
            #cv2.imshow("Facerecognition", frame)
            if update_timer.time_has_elpsed(): # Jede Sekunde sollen die Settings aktualisiert werden.
                self.__settings = self.__data.get_settings()
                update_timer.reset()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cap.release()
                cv2.destroyAllWindows()
                del self.exec_net
                del self.exec_net_reid
                break

class Timer:

    def __init__(self, seconds):
        self.__m_seconds = seconds
        self.__m_time_stamp = None

    def time_has_elpsed(self):
        if not self.__m_time_stamp:
            return True
        return (time.time() - self.__m_time_stamp) >= self.__m_seconds

    def reset(self):
        self.__m_time_stamp = time.time()
