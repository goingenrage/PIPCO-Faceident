import sys
from scipy.spatial import distance
import os
import cv2
from argparse import ArgumentParser
import json
from openvino.inference_engine import IENetwork, IEPlugin
from pathlib import Path

model_xml = '../models/face-detection-adas-0001.xml'
model_bin = '../models/face-detection-adas-0001.bin'
model_reid_xml = '../models/face-reidentification-retail-0095.xml'
model_reid_bin = '../models/face-reidentification-retail-0095.bin'

globalReIdVec = []
names = {}
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

def buildargparser():
    parser = ArgumentParser()

    parser.add_argument("-pg", "--person_gallery", help="Pfad zum vorbereitetem person_gallery.json file", default=None)

    return parser


def personGallery(face_gallery):
    print(face_gallery)
    with open(face_gallery, "r") as read_file:
        faces = json.load(read_file)
    print(face_gallery)

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
            reId = reidentification(image)
            globalReIdVec.append(reId)
            names[id] = label
            id += 1


def initReidentification():
    global exec_net, exec_net_reid, input_blob, out_blob, model_n, model_c, model_h, model_w,input_blob_reid,out_blob_reid,model_reid_n, model_reid_c, model_reid_h, model_reid_w
    net = IENetwork(model=model_xml, weights=model_bin)
    net_reid = IENetwork(model=model_reid_xml, weights=model_reid_bin)

    plugin = IEPlugin(device="CPU")
    plugin.add_cpu_extension(
        "/home/reichenecker/inference_engine_samples_build/intel64/Release/lib/libcpu_extension.so")
    plugin_reid = IEPlugin(device="CPU")
    plugin_reid.add_cpu_extension(
        "/home/reichenecker/inference_engine_samples_build/intel64/Release/lib/libcpu_extension.so")
    plugin_reid.set_config(net_reid)
    exec_net = plugin.load(network=net, num_requests=1)
    exec_net_reid = plugin_reid.load(network=net_reid, num_requests=1)

    input_blob = next(iter(net.inputs))
    out_blob = next(iter(net.outputs))
    print('network.inputs = ' + str(list(net.inputs)))
    print('network.outputs = ' + str(list(net.outputs)))
    model_n, model_c, model_h, model_w = net.inputs[input_blob].shape

    input_blob_reid = next(iter(net_reid.inputs))
    out_blob_reid = next(iter(net_reid.outputs))

    model_reid_n, model_reid_c, model_reid_h, model_reid_w = net_reid.inputs[input_blob_reid].shape

    print('network.inputs = ' + str(list(net_reid.inputs)))
    print('network.outputs = ' + str(list(net_reid.outputs)))


def reidentification(image):


    im = cv2.resize(image, (640, 480))

    in_frame = cv2.resize(im, (model_w, model_h))
    in_frame = in_frame.transpose((2, 0, 1))
    in_frame = in_frame.reshape((model_n, model_c, model_h, model_w))

    exec_net.start_async(request_id=0, inputs={input_blob: in_frame})

    if exec_net.requests[0].wait(-1) == 0:
        res = exec_net.requests[0].outputs[out_blob]
        for obj in res[0][0]:
            class_id = int(obj[1])
            if class_id == 1:
                if obj[2] > 0.5:
                    xmin = int(obj[3] * 640)
                    ymin = int(obj[4] * 480)
                    xmax = int(obj[5] * 640)
                    ymax = int(obj[6] * 480)
                    frame_org = im.copy()
                    person = frame_org[ymin:ymax, xmin:xmax]
                    in_frame_reid = cv2.resize(person, (model_reid_w, model_reid_h))
                    in_frame_reid = in_frame_reid.transpose((2, 0, 1))  # Change data layout from HWC to CHW
                    in_frame_reid = in_frame_reid.reshape((model_reid_n, model_reid_c, model_reid_h, model_reid_w))

                    exec_net_reid.start_async(request_id=0, inputs={input_blob_reid: in_frame_reid})

                    if exec_net_reid.requests[0].wait(-1) == 0:
                        res_reid = exec_net_reid.requests[0].outputs[out_blob_reid]
                        reIdVector = res_reid[0].reshape(-1, )

                        return reIdVector


def createMatchingPerson(newReIdVec):
    global globalReIdVec
    size = len(globalReIdVec)

    globalReIdVec.append(newReIdVec)
    return len(globalReIdVec) - 1


def findMatchingPerson(newReIdVec):
    global globalReIdVec
    size = len(globalReIdVec)
    # print(newReIdVec)
    # print("size=" + str(size))

    idx = size
    for i in range(size):

        cosSim = cosineSimilarity(newReIdVec, globalReIdVec[i])
        print(cosSim)
        if cosSim > 0.5:
            # globalReIdVec[i] = newReIdVec.copy() #ist es sinnvoll bei einem erkannten gesicht den vector zu aktualisieren?
            # was passiert bei einer falschen erkennung?
            idx = i
            break

    if idx < size:
        return idx
    else:
        return -1


def cosineSimilarity(u,
                     v):  # Durch die Berechnung der Cosinus-Ähnlichkeit (siehe https://en.wikipedia.org/wiki/Cosine_similarity) wird verglichen,
    # ob die beiden Vectoren ähnlich sind.
    return float(1 - distance.cosine(u, v))


def main():
    global exec_net, exec_net_reid
    args = buildargparser().parse_args();
    initReidentification()
    personGallery(args.person_gallery)
    #loadAllowedFaces()

    cap = cv2.VideoCapture(0)
    print("init done")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cap_w = cap.get(3)
        cap_h = cap.get(4)
        in_frame = cv2.resize(frame, (model_w, model_h))
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape((model_n, model_c, model_h, model_w))

        exec_net.start_async(request_id=0, inputs={input_blob: in_frame})

        if exec_net.requests[0].wait(-1) == 0:
            res = exec_net.requests[0].outputs[out_blob]

            for obj in res[0][0]:
                class_id = int(obj[1])
                if class_id == 1:
                    if obj[2] > 0.5:
                        xmin = int(obj[3] * cap_w)
                        ymin = int(obj[4] * cap_h)
                        xmax = int(obj[5] * cap_w)
                        ymax = int(obj[6] * cap_h)

                        frame_org = frame.copy()
                        person = frame_org[ymin:ymax, xmin:xmax]
                        in_frame_reid = cv2.resize(person, (model_reid_w, model_reid_h))
                        in_frame_reid = in_frame_reid.transpose((2, 0, 1))
                        in_frame_reid = in_frame_reid.reshape((model_reid_n, model_reid_c, model_reid_h, model_reid_w))
                        cv2.imshow("eksde", person)

                        exec_net_reid.start_async(request_id=0, inputs={input_blob_reid: in_frame_reid})
                        foundId = 1;
                        if exec_net_reid.requests[0].wait(-1) == 0:
                            res_reid = exec_net_reid.requests[0].outputs[out_blob_reid]
                            reIdVector = res_reid[0].reshape(-1, )
                            # print(reIdVector)
                            foundId = findMatchingPerson(reIdVector)

                        color = (255, 0, 0)
                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                        idColor = (0, 0, 255)
                        print(foundId)
                        if foundId is not -1:
                            cv2.putText(frame, names[foundId], (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8, idColor,
                                        1)
                        else:
                            cv2.putText(frame, "Unknown", (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.8, idColor, 1)

        cv2.imshow("Facerecognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            break

    cv2.destroyAllWindows()
    del exec_net
    del exec_net_reid


if __name__ == '__main__':
    sys.exit(main() or 0)
