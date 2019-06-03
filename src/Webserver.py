from flask import Flask, Response, request, send_from_directory, jsonify
import time
import json
import base64
from flask_cors import CORS
from Daten import Daten

class Webserver:
    ERROR = 'ERROR', 403

    def __init__(self):
        """Setup flask server - register all possible rest enquiries"""
        self.app = Flask(__name__, root_path="")
        self.app.add_url_rule('/videostream', 'video_feed', self.video_feed, methods=["GET"])

        self.app.after_request(self.add_header)
        CORS(self.app)
        self.data = Daten.get_instance()

    def add_header(self, r):
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    def gen(self):
        """Creates generator object with returning frames"""
        while True:
            #print("test")
            time.sleep(1 / 30)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.data.get_image().tobytes() + b'\r\n\r\n')



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


    def video_feed(self):
        if self.data.get_image() is not None:
            return Response(self.gen(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')
        return "no images available"


def response(val):
    return Response(response=val,
                    status=200,
                    mimetype="application/json")

