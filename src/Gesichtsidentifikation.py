import cv2
import numpy as np
import threading
import face_recognition
import sys




class Gesichtsidentifikation:

    moreFaces = True
    bekanntesGesicht = False
    imgName = 'test'
    imgEnding = '.jpg'
    imgNumber = 123123
    rectsTest = []
    capture = None
    face_cascade = None
    font = None
    encoding = face_recognition.face_encodings(cv2.resize(cv2.imread('../Testbilder/test123123.jpg'), (0,0), fx=0.25, fy=0.25))[0]
    #init Funktion (vergleichbar mit Konstruktor?) Wird beim erzeugen des Objekts ausgefuehrt.
    def __init__(self, normal=True):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640);
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480);
        self.face_cascade = cv2.CascadeClassifier(
            '/opt/intel/computer_vision_sdk_2018.5.455/opencv/etc/haarcascades/haarcascade_frontalface_default.xml')
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.load_approved_faces()

    #Wenn im uebergebenen img ein Gesicht erkannt wird, wird dieses Gesicht zurueckgegeben
    def detect_face(self, img, cascade):
        rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30),
                                         flags=cv2.CASCADE_SCALE_IMAGE)
        if len(rects) == 0:
            return []
        rects[:,2:] += rects[:,:2]
        return rects

    #Auf dem auszugebenen Bild wird ein Rechteck um die erkannte Gesichtsform gezeichnet und zudem als Text markiert, ob
    #dieses Gesicht freigegeben ist oder nicht.
    def draw_rects(self,img, rects, color, text):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        cv2.putText(img, text,(x1, y1-5), self.font, 1, color, 2)

    #verkleinert das aufgenommene Bild auf die groesse der erkannten Gesichtsform (kann genutzt werden um neue erlaubte
    #Gesichter in die Datenbank aufzunehmen?)
    def show_small_image(rects, frame):
        margin = 40
        yfhd = 1080
        xfhd = 1920
        iface = 0
        nfaces = 0

        for x1, y1, x2, y2 in rects:
            x5 = x1
            iface = iface + 1
            nfaces = nfaces + 1
            sface = "_%02d" % iface
    #        filename = strftime("%Y%m%d_%H_%M_%S") + sface + ".jpg"
            yf1 = -margin + y1
            if yf1 < 0:
                yf1 = 0
            yf2 = y2 + margin
            if yf2 >= yfhd:
                yf1 = yfhd - 1

            xf1 = -margin + x1
            if xf1 < 0:
                xf1 = 0
            xf2 = x2 + margin
            if xf2 >= xfhd:
                xf2 = xfhd - 1
            crop_img = frame[yf1:yf2, xf1:xf2]
            # cv2.imwrite("test123123.jpg", crop_img)
            cv2.imshow('HELLO', crop_img)

    #Liest alle Gesichter ein, die erkannt werden duerfen und speichert sie in eine Liste
    def load_approved_faces(self):
        self.imgNumber = 123122
        self.rectsTest.clear()
        while True:

            img = cv2.imread(self.imgName + str(self.imgNumber) + self.imgEnding)
            #print('xD' + str(sys.getsizeof(self.rectsTest)))
            # img = cv2.imread('test123123.jpg')
            self.rectsTest.append(self.detect_face(img, self.face_cascade))
            self.imgNumber = self.imgNumber + 1
            if img is None:
                break

    #prueft, ob die beiden uebergebenen Gesichter uebereinstimmen. Gibt True bei uebereinstimmung und False bei keiner
    #uebereinstimmung zurueck.
    def face_identification(self,test_face):
        #print('eksdeeee ' + str(face.all()))
        small_frame = cv2.resize(test_face, (0,0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:,:,::-1]
        encoding_test = face_recognition.face_encodings(rgb_small_frame)[0]
        test = False
        for xd in encoding_test:
            results = face_recognition.compare_faces(self.encoding, xd)
            if True in results:
                test = True
                break
            else:
                test = False
        return test

    def start(self):

        while(True):
            ret, frame = self.capture.read()
            #print('retval: ' + str(ret))

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = self.detect_face(gray, self.face_cascade)
            #print(sys.getsizeof(rects))
            if len(rects):
                #vis = frame.copy() #Kopie des aktuellen Frames wird erstellt um darauf zu Zeichnen

                #draw_rectangle(rects, gray)

                #print('Gesicht erkannt!')


                if True:
                    #print('test123')
                    test_face = frame


                    #test = self.face_identification(test_face)
                    if True:
                        bekanntesGesicht = True
                    else:
                        bekanntesGesicht = False

                    if bekanntesGesicht:
                        print('Bekanntes Gesicht gesehen!')
                        self.draw_rects(frame, rects, (0, 255, 0), 'Erlaubt')
                    else:
                        print('Unbekanntes Gesicht gesehen!')
                        self.draw_rects(frame, rects, (0, 255, 0), 'nicht Erlaubt')

                cv2.imshow('HELLO', frame)

            else:
                #print('kein gesicht erkannt!')
                cv2.imshow('HELLO', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.capture.release()
                cv2.destroyAllWindows()
                break

