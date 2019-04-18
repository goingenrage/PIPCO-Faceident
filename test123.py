import cv2
import os
import sys
import numpy as np

namen = ["", "admars", "ahodki", "slbirc", "valentin"]


def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30),
                                     flags=cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects

def detect_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier('/opt/intel/computer_vision_sdk_2018.5.455/opencv/etc/haarcascades/haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5);
    if (len(faces) == 0):
        return 0,0
    (x, y, w, h) = faces[0]

    return gray[y:y + w, x:x + h], faces[0]

def prepare_training_data(data_folder_path):

    dirs = os.listdir(data_folder_path)
    faces = []
    labels = []

    for dir_name in dirs:

        if not dir_name.startswith("s"):
            continue;
        label = int(dir_name.replace("s", ""))
        subject_dir_path = data_folder_path + "/" + dir_name

        subject_images_names = os.listdir(subject_dir_path)
        for image_name in subject_images_names:
            if image_name.startswith("."):
                continue;
            image_path = subject_dir_path + "/" + image_name
            image = cv2.imread(image_path)
            cv2.imshow("Training on image...", image)
            cv2.waitKey(100)
            face, rect = detect_face(image)

        if face is not None:
            faces.append(face)
            labels.append(label)

    cv2.destroyAllWindows()
    cv2.waitKey(1)
    cv2.destroyAllWindows()

    return faces, labels




def identifiziere(test_img, confidence):

    img = test_img.copy()
    face, rect = detect_face(img)
    try:
        if not face.any() == None:
            label = face_recognizer.predict(face)
            print(label)
            if 100 - label[1] >= confidence:
                name = namen[label[0]]
            else:
                name = "unknown"
            (x, y, w, h) = rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, name, (rect[0],rect[1] -5), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
    except:
        print(sys.exc_info()[0])

    return img





face_recognizer = cv2.face.LBPHFaceRecognizer_create()
def trainiereFaceRecognizer():

    faces, labels = prepare_training_data("/home/reichenecker/Dokumente/Semesterprojekt2019/test")
    face_recognizer.train(faces, np.array(labels))
    face_recognizer.save('trainedModel.xml')

def ladeFaceRecognizer():
    face_recognizer.read('trainedModel.xml')


#trainiereFaceRecognizer()
ladeFaceRecognizer()

capture = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(
            '/opt/intel/computer_vision_sdk_2018.5.455/opencv/etc/haarcascades/haarcascade_frontalface_default.xml')
while(True):
            ret, frame = capture.read()
            #print('retval: ' + str(ret))


            rects = detect(frame, face_cascade)
            #print(sys.getsizeof(rects))
            if len(rects):
                #vis = frame.copy() #Kopie des aktuellen Frames wird erstellt um darauf zu Zeichnen

                #draw_rectangle(rects, gray)

                print('Gesicht erkannt!')




                cv2.imshow('HELLO', identifiziere(frame, 40))

            else:
                print('kein gesicht erkannt!')
                cv2.imshow('HELLO', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                capture.release()
                cv2.destroyAllWindows()
                break


