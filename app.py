# Author: Lim Kha Shing
# Reference
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py
# https://github.com/ageitgey/face_recognition/wiki/Calculating-Accuracy-as-a-Percentage

import os

import cv2
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename

from image_processing import compare_face
from constants import *

app = Flask(__name__)


def get_error_result(source_type, is_no_files):
    if is_no_files:
        result = {
                "status_code": 400,
                "error": "No " + source_type + " Found"
            }
    else:
        result = {
            "status_code": 400,
            "error": source_type + " extension is not correct"
        }
    return jsonify(result)


@app.route('/api/upload', methods=['POST'])
def upload_image_video():
    # Check if a valid image and video file was uploaded
    if request.method == 'POST':

        if request.files['known'].filename == '':
            print("no files in known")
            return get_error_result("Image", True)

        if request.files['unknown'].filename == '':
            print("no files in unknown")
            return get_error_result("Video", True)

        known = request.files['known']
        unknown = request.files['unknown']
        threshold = request.form['threshold']

        if not known.filename.lower().endswith(ALLOWED__PICTURE_EXTENSIONS):
            print(known.filename)
            return get_error_result("Image", False)

        if not unknown.filename.lower().endswith(ALLOWED_VIDEO_EXTENSIONS):
            print(unknown.filename)
            return get_error_result("Video", False)

        # Check if upload and frames folder existed or not.
        # If not then create it
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        if not os.path.exists(frames_folder):
            os.makedirs(frames_folder)

        unknown_filename = secure_filename(unknown.filename)

        unknown.save(os.path.join(upload_folder, unknown_filename))
        known.save(os.path.join(upload_folder, known.filename))

        if known and unknown:

            # Resize the known image and scale it down
            known_image_size = os.stat(os.path.join(upload_folder, known.filename)).st_size
            print("Image Size: ", known_image_size)

            if known_image_size > image_size_threshold:
                print("Resizing the known image")
                known_image = cv2.imread(os.path.join(upload_folder, known.filename))
                resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
                cv2.imwrite(os.path.join(upload_folder, known.filename), resized_image)

            if threshold == '':
                print("Threshold is blank. Use default 0.6")
                return compare_face(os.path.join(upload_folder, known.filename), unknown_filename)
            print("Threshold is specified. Use " + threshold)
            return compare_face(os.path.join(upload_folder, known.filename), unknown_filename, float(threshold))


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # add own IPV4 address for debug
    app.run(host="192.168.0.161", debug=True)
