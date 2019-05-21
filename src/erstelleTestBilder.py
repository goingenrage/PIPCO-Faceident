import cv2
import numpy as np
import threading
import face_recognition
import sys


i = 0


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
        return crop_img
capture = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(
            '/opt/intel/openvino_2019.1.133/opencv/etc/haarcascades/haarcascade_frontalface_default.xml')
def detect_face(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30),
                                     flags=cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects
print("speichern der bilder beginnt!")
while i < 10:
    ret, frame = capture.read()
    # print('retval: ' + str(ret))
    cv2.imshow("Facerecognition", frame)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detect_face(gray, face_cascade)
    # print(sys.getsizeof(rects))
    if len(rects):
        i = i +1
        filename = "jack." + str(i) + ".jpg"
        print(filename)
        cv2.imwrite(filename, show_small_image(rects, frame))
        print("bild gespeichert")

print("20 bilder gespeichert!")