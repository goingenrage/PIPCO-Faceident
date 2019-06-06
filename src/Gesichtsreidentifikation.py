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
from src.Mail import Mail


from scripts import interfacedb


class Gesichtsreidentifikation(Thread):


    model_xml = ""
    model_bin = ""
    model_reid_xml = ""
    model_reid_bin = ""
    path_to_database = ""
    path_to_tmpfolder = ""
    path_to_cpuextension = ""
    path_to_outputvid = ""

    globalReIdVec = []
    unknownPersons = []
    unknownRecentlySeen = {}
    names = {}
    face_gallery = ""
    recentlySeen = {}
    model_n = 0
    model_c = 0
    model_h = 0
    model_w = 0
    model_reid_n = 0
    model_reid_c = 0
    model_reid_h = 0
    model_reid_w = 0
    input_blob_reid = []
    out_blob_reid = []
    input_blob = []
    out_blob = []
    exec_net = []
    exec_net_reid = []
    cap = None
    config_path = ""
    path_to_camera = ""


    def __init__(self, config_path):
        self.config_path = config_path
        self.data = PipcoDaten.get_instance()
        self.mailing = Mail()
        super(Gesichtsreidentifikation, self).__init__()


    def init_variables(self):
        config = configparser.RawConfigParser()
        config.read(self.config_path)

        self.face_gallery = config.get('DEFAULT', 'face_gallery')
        self.model_xml = config.get('DEFAULT', 'model_xml')

        self.model_bin = config.get('DEFAULT', 'model_bin')


        self.model_reid_xml = config.get('DEFAULT', 'model_reid_xml')

        self.model_reid_bin = config.get('DEFAULT', 'model_reid_bin')


        self.path_to_database = config.get('DEFAULT', 'path_to_database')

        self.path_to_tmpfolder = config.get('DEFAULT', 'path_to_tmpfolder')

        self.path_to_camera = config.get('DEFAULT', 'path_to_camera')
        self.path_to_cpuextension = config.get('DEFAULT', 'path_to_cpuextension')
        self.path_to_outputvid = config.get('DEFAULT', 'path_to_outputvid')


    def __clearDirectory(self):
        folder = self.path_to_tmpfolder
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)


    def getImagesFromDatabase(self):
        print("Hole Bilder aus Datenbank")

        self.__clearDirectory()
        interfacedb.initialize(self.path_to_database, self.path_to_tmpfolder)
        interfacedb.database_connect()
        interfacedb.get_all_pictures()

        ##create_list.create_list(self.path_to_tmpfolder)


    def personGallery(self):
        #getImagesFromDatabase()
        create_list.create_list(self.path_to_tmpfolder)
        with open(self.face_gallery, "r") as read_file:
            faces = json.load(read_file)
        print(self.face_gallery)

        id = 0
        print(faces)
        for face in faces:
            print(face)
            label = face
            for path in faces[face]:
                config = Path(path)
                if not config.is_file():
                    break

                image = cv2.imread(path)
                _, _, _, _, reId = self.reidentification(image)
                self.globalReIdVec.append(reId)
                self.names[id] = label
                id += 1


    def initReidentification(self):
        if self.path_to_camera == '0':
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(self.path_to_camera)
        net = IENetwork(model=self.model_xml, weights=self.model_bin)
        net_reid = IENetwork(model=self.model_reid_xml, weights=self.model_reid_bin)

        plugin = IEPlugin(device="CPU")
        plugin.add_cpu_extension(self.path_to_cpuextension)
        plugin_reid = IEPlugin(device="CPU")
        plugin_reid.add_cpu_extension(self.path_to_cpuextension)
        # plugin_reid.set_config(net_reid)
        self.exec_net = plugin.load(network=net, num_requests=1)
        self.exec_net_reid = plugin_reid.load(network=net_reid, num_requests=1)

        self.input_blob = next(iter(net.inputs))
        self.out_blob = next(iter(net.outputs))
        print('network.inputs = ' + str(list(net.inputs)))
        print('network.outputs = ' + str(list(net.outputs)))
        self.model_n, self.model_c, self.model_h, self.model_w = net.inputs[self.input_blob].shape

        self.input_blob_reid = next(iter(net_reid.inputs))
        self.out_blob_reid = next(iter(net_reid.outputs))

        self.model_reid_n, self.model_reid_c, self.model_reid_h, self.model_reid_w = net_reid.inputs[self.input_blob_reid].shape

        print('network.inputs = ' + str(list(net_reid.inputs)))
        print('network.outputs = ' + str(list(net_reid.outputs)))


    def reidentification(self,image):

        cap_w = self.cap.get(3)
        cap_h = self.cap.get(4)
        im = cv2.resize(image, (640, 480))

        in_frame = cv2.resize(im, (self.model_w, self.model_h))
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape((self.model_n, self.model_c, self.model_h, self.model_w))

        self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame})
        try:
            if self.exec_net.requests[0].wait(-1) == 0:
                res = self.exec_net.requests[0].outputs[self.out_blob]
                for obj in res[0][0]:
                    class_id = int(obj[1])
                    if class_id == 1:
                        if obj[2] > 0.5:
                            xmin = int(obj[3] * cap_w)
                            ymin = int(obj[4] * cap_h)
                            xmax = int(obj[5] * cap_w)
                            ymax = int(obj[6] * cap_h)
                            frame_org = im.copy()
                            person = frame_org[ymin:ymax, xmin:xmax]
                            in_frame_reid = cv2.resize(person, (self.model_reid_w, self.model_reid_h))
                            in_frame_reid = in_frame_reid.transpose((2, 0, 1))  # Change data layout from HWC to CHW
                            in_frame_reid = in_frame_reid.reshape((self.model_reid_n, self.model_reid_c, self.model_reid_h, self.model_reid_w))

                            self.exec_net_reid.start_async(request_id=0, inputs={self.input_blob_reid: in_frame_reid})

                            if self.exec_net_reid.requests[0].wait(-1) == 0:
                                res_reid = self.exec_net_reid.requests[0].outputs[self.out_blob_reid]
                                reIdVector = res_reid[0].reshape(-1, )

                                return xmin, ymin, xmax, ymax, reIdVector
        except Exception as e:
            print("exception")
        return 0, 0, 0, 0, None


    def createMatchingPerson(self, newReIdVec):

        size = len(self.globalReIdVec)

        self.globalReIdVec.append(newReIdVec)
        return len(self.globalReIdVec) - 1


    def findMatchingPerson(self, newReIdVec):

        size = len(self.globalReIdVec)
        idx = size
        for i in range(size):

            cosSim = self.cosineSimilarity(newReIdVec, self.globalReIdVec[i])
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


    def cosineSimilarity(self, u,v):
        # Durch die Berechnung der Cosinus-Ähnlichkeit (siehe https://en.wikipedia.org/wiki/Cosine_similarity) wird verglichen,
        # ob die beiden Vectoren ähnlich sind.
        return float(1 - distance.cosine(u, v))

    def isUnknown(self, reIdVec):
        size = len(self.unknownPersons)
        for i in range(size):
           if self.cosineSimilarity(reIdVec, self.unknownPersons[i]) > 0.5:
               return i, False
        return -1, True


    def run(self):


        self.init_variables()
        self.initReidentification()
        self.personGallery()
        filename = ""
        start_recording = False
        start_time = 0
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = None
        #self.cap = cv2.VideoCapture("http://192.168.0.35/cgi-bin/videostream.cgi?user=admin&pwd=admin")
        print("init done")

        reallyUnknown = 0;
        while True:


            ret, frame = self.cap.read()
            if not ret:
                break
            ret2, jpg = cv2.imencode('.jpg', frame)
            self.data.set_image_without(jpg)
            cap_w = self.cap.get(3)
            cap_h = self.cap.get(4)
            in_frame = cv2.resize(frame, (self.model_w, self.model_h))
            in_frame = in_frame.transpose((2, 0, 1))
            in_frame = in_frame.reshape((self.model_n, self.model_c, self.model_h, self.model_w))

            self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame})
            allowed_person_in_room = False
            unallowed_person_in_room = False
            if self.exec_net.requests[0].wait(-1) == 0:

                res = self.exec_net.requests[0].outputs[self.out_blob]

                for obj in res[0][0]:
                    try:
                        class_id = int(obj[1])
                        if class_id == 1:
                            if obj[2] > 0.5:
                                xmin = int(obj[3] * cap_w)
                                ymin = int(obj[4] * cap_h)
                                xmax = int(obj[5] * cap_w)
                                ymax = int(obj[6] * cap_h)
                                frame_org = frame.copy()
                                person = frame_org[ymin:ymax, xmin:xmax]
                                in_frame_reid = cv2.resize(person, (self.model_reid_w, self.model_reid_h))
                                in_frame_reid = in_frame_reid.transpose((2, 0, 1))
                                in_frame_reid = in_frame_reid.reshape(
                                    (self.model_reid_n, self.model_reid_c, self.model_reid_h, self.model_reid_w))

                                self.exec_net_reid.start_async(request_id=0, inputs={self.input_blob_reid: in_frame_reid})

                                if self.exec_net_reid.requests[0].wait(-1) == 0:
                                    res_reid = self.exec_net_reid.requests[0].outputs[self.out_blob_reid]
                                    reIdVector = res_reid[0].reshape(-1, )

                                    foundId = self.findMatchingPerson(reIdVector)

                                    color = (255, 0, 0)
                                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                                    idColor = (0, 0, 255)
                                    #print(foundId)
                                    if foundId is not -1:
                                        cv2.putText(frame, self.names[foundId], (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                    idColor,
                                                    1)
                                        allowed_person_in_room = True
                                        #Hier soll geprüft werden, wann die Person zuletzt gesehen wurde, um Aktionen nicht bei jedem Frame auszuführen.
                                        if not self.recentlySeen.__contains__(self.names[foundId]) or (time.time() - self.recentlySeen[self.names[foundId]]) > 10:
                                            print("Person " + self.names[foundId] + " wurde erkannt!")
                                            logging.info("Person " + self.names[foundId] + " wurde erkannt!")
                                            self.recentlySeen[self.names[foundId]] = time.time()



                                    else:
                                        reallyUnknown = reallyUnknown +1
                                        unknownID,tmp = self.isUnknown(reIdVector)
                                        if reallyUnknown > 10 and tmp:
                                            reallyUnknown = 0
                                            unallowed_person_in_room = True
                                            self.unknownPersons.append(reIdVector)
                                            self.unknownRecentlySeen[len(self.unknownPersons)-1] = time.time()
                                            print("Unbekannte Person entdeckt!")
                                            self.mailing.send_message("ACHTUNG!", "Unbekannte Person entdeckt!", "test")
                                            logging.warning("Unbekannte Person entdeckt!")
                                            cv2.putText(frame, "Unknown", (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                        idColor, 1)
                                        if tmp == False:
                                            reallyUnknown = 0
                                            unallowed_person_in_room = True
                                            if time.time() - self.unknownRecentlySeen[unknownID] > 100:
                                                self.unknownRecentlySeen[unknownID] = time.time()
                                                print("Unbefugte Person wurde zuvor erkannt")
                                                logging.warning("Unbefugte Person wurde zuvor erkannt")
                                            cv2.putText(frame, str(unknownID), (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                                        idColor, 1)


                    except Exception as e:
                        print("exception in main" + str(e))
                # print(str(allowed_person_in_room) + " " + str(unallowed_person_in_room))
                if not start_recording and allowed_person_in_room and unallowed_person_in_room:
                    print("Start recording with allowed person...")
                    start_recording = True
                    start_time = time.time()
                    filename = time.strftime("mit_berechtigtem_%d_%m_%Y_%H_%M_%S")
                    out = cv2.VideoWriter(self.path_to_outputvid + filename + '.avi', fourcc, 20.0, (640, 480))
                if not start_recording and unallowed_person_in_room and not allowed_person_in_room:
                    print("Start recording...")
                    start_recording = True
                    start_time = time.time()
                    filename = time.strftime("ohne_berechtigtem_%d_%m_%Y_%H_%M_%S")
                    out = cv2.VideoWriter(self.path_to_outputvid + filename + '.avi', fourcc, 20.0, (640, 480))

                if start_recording:
                    out.write(frame)
                    if time.time() - start_time > 50:
                        start_recording = False
                        print("Recording end...")
            ret2, jpg = cv2.imencode('.jpg', frame)
            self.data.set_image_fr(jpg)
            cv2.imshow("Facerecognition", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cap.release()
                cv2.destroyAllWindows()
                del self.exec_net
                del self.exec_net_reid
                break

