from flask import Flask, Response, request, send_from_directory, jsonify
from src.DataStorage import *
import json
import base64
from flask_cors import CORS
import time
from src.ImageProcessing import THUMBNAIL_TYPE, RECORDING_TYPE
from src.DataPersistence import DataPersistence

# https://github.com/desertfury/flask-opencv-streaming

class Webserver:

    ERROR = 'ERROR', 403

    def __init__(self):
        """Setup flask server - register all possible rest enquiries"""
        self.app = Flask(__name__, root_path="")
        self.app.add_url_rule('/videostream', 'video_feed', self.video_feed, methods=["GET"])
        self.app.add_url_rule('/logs/<page_no>/<batch_size>', 'get_logs', self.get_logs, methods=["GET"])
        self.app.add_url_rule('/log/<log_id>', 'delete_log', self.delete_log, methods=["DELETE"])
        self.app.add_url_rule('/mail', 'add_mail', self.add_mail, methods=["POST"])
        self.app.add_url_rule('/mails', 'get_mails', self.get_mails, methods=["GET"])
        self.app.add_url_rule('/mail/<mail_id>', 'delete_mail', self.delete_change_mail, methods=["DELETE", "PUT"])
        self.app.add_url_rule('/login', 'check_login', self.check_login, methods=["POST"])
        self.app.add_url_rule('/config', 'change_get_config', self.change_get_config, methods=["POST", "GET"])
        self.app.add_url_rule('/recording/<path:filename>', 'recording', self.get_recording, methods=["GET"])
        self.app.add_url_rule('/backup', 'backup', self.get_backup, methods=["GET"])
        self.app.after_request(self.add_header)
        CORS(self.app)
        self.data = PipcoDaten.get_instance()
        self.settings = self.data.get_settings()
        self.local_cam_mode = int(self.settings.cam_mode)

    def add_header(self, r):
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    def gen(self):
        print("in gen...")
        """Creates generator object with returning frames"""
        x = self.local_cam_mode
        while True:
                time.sleep(1/self.data.m_stream_fps)

                #print(self.local_cam_mode)
                if self.local_cam_mode == 0:
                    frame = self.data.get_image_without().tobytes()
                if self.local_cam_mode == 1:
                    frame = self.data.get_image().tobytes()
                if self.local_cam_mode == 2:
                    frame = self.data.get_image_fr().tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')





    def get_recording(self, filename):
        return send_from_directory("data/recordings/", filename, mimetype="video/mp4")

    def get_backup(self):
        with self.data.lock_all():
            DataPersistence.zip_current_data()
            return send_from_directory(".", "backup.zip", mimetype="application/zip")

    def get_mails(self):
        return response(json.dumps(list(self.data.get_mails().values()), cls=MessageEncoder))

    def change_get_config(self):
        try:

            if request.method == 'POST':
                print("change_get_config: POST")
                data = request.get_json()
                sensitivity = data.get('sensitivity')
                streamaddress = data.get('streamaddress')
                brightness = data.get('brightness')
                contrast = data.get('contrast')
                global_notify = data.get('global_notify')
                max_storage = data.get('max_storage')
                max_logs = data.get('max_logs')
                cliplength = data.get('cliplength')
                log_enabled = data.get('log_enabled')
                fr_log_enabled = data.get('fr_log_enabled')
                cam_mode = data.get('cam_mode')
                #self.local_cam_mode = int(cam_mode)
                return response(json.dumps(self.data.change_settings(sensitivity, brightness, contrast, streamaddress,
                                                                     global_notify, log_enabled, fr_log_enabled, cliplength, max_logs, max_storage, cam_mode)))
            else:
                print("change_get_config: GET")
                return response(json.dumps(self.data.get_settings(), cls=MessageEncoder))
        except Exception:
            return Webserver.ERROR

    def delete_change_mail(self, mail_id):
        try:
            if request.method == 'DELETE':
                return jsonify(mail_id=self.data.remove_mail(int(mail_id)))
            else:
                return jsonify(notify=self.data.toggle_mail_notify(int(mail_id)))
        except Exception:
            return Webserver.ERROR

    def add_mail(self):
        try:
            mailaddress = request.get_json().get('mail')
            if mailaddress:
                ret = self.data.add_mail(mailaddress)
                if ret != -1:
                    return jsonify(mail_id=ret)
            return Webserver.ERROR
        except Exception:
            return Webserver.ERROR

    def check_login(self):
        try:
            data = request.get_json()
            user = data.get('user')
            password = data.get('password')
            if self.data.check_login(user, password):
                return jsonify(status="OK")
            return Webserver.ERROR
        except Exception:
            return Webserver.ERROR

    def delete_log(self, log_id):
        try:
            id = self.data.remove_log(int(log_id))
            return jsonify(log_id=id)
        except Exception:
            return Webserver.ERROR

    def get_logs(self,page_no, batch_size):
        return response(json.dumps(list(self.data.get_log_page(page_no,batch_size).values()), cls=MessageEncoder))

    def video_feed(self):

        print("in video_feed...")

        return Response(self.gen(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')


        return "no images available"


def response(val):
    return Response(response=val,
             status=200,
             mimetype="application/json")


class MessageEncoder(json.JSONEncoder):
    """Encode objects and change the presentation of logs for message"""
    def default(self, o):
        if isinstance(o, Log):
            thumbnail = THUMBNAIL_PATH + str(o.id) + THUMBNAIL_TYPE
            recording = str(o.id) + RECORDING_TYPE
            try:
                with open(thumbnail, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception:
                encoded_string = ""
            return {"id": o.id,
                    "message": o.message,
                    "timestamp": o.timestamp,
                    "thumbnail": encoded_string,
                    "recording": recording}
        else:
            return o.__dict__