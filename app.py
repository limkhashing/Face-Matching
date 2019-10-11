# Author: Lim Kha Shing
# Reference
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py

import os

import cv2
import request_id
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from request_id import RequestIdMiddleware
from image_processing import compare_face
from constants import *
from werkzeug.serving import make_server

app = Flask(__name__)

middleware = RequestIdMiddleware(
    app,
    format='{status} {REQUEST_METHOD:<6} {REQUEST_PATH:<60} {REQUEST_ID}',
)


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


def createDirectories():
    # Check if upload and frames folder existed or not.
    # If not then create it
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)

    # Get unique Request ID
    face_matching_request_id = request_id.get_request_id(request)
    print("Request ID:", face_matching_request_id)

    # create a subdirectory for frames and upload folder
    request_upload_folder_path = os.path.join(upload_folder, face_matching_request_id)
    request_frames_folder_path = os.path.join(frames_folder, face_matching_request_id)
    os.makedirs(request_frames_folder_path)
    os.makedirs(request_upload_folder_path)

    return request_upload_folder_path, request_frames_folder_path


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

        request_upload_folder_path, request_frames_folder_path = createDirectories()
        unknown_filename = secure_filename(unknown.filename)

        unknown_filename_path = os.path.join(request_upload_folder_path, unknown_filename)
        known_filename_path = os.path.join(request_upload_folder_path, known.filename)

        unknown.save(unknown_filename_path)
        known.save(known_filename_path)

        if known and unknown:

            # Resize the known image and scale it down
            known_image_size = os.stat(known_filename_path).st_size
            print("Image Size: ", known_image_size)

            if known_image_size > image_size_threshold:
                print("Resizing the known image")
                known_image = cv2.imread(known_filename_path)
                resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
                cv2.imwrite(known_filename_path, resized_image)

            video_path = os.path.join(request_upload_folder_path, unknown_filename)

            if threshold == '':
                print("Threshold is blank. Use default 0.6")
                return compare_face(known_filename_path,
                                    video_path,
                                    request_upload_folder_path,
                                    request_frames_folder_path)
            print("Threshold is specified. Use " + threshold)
            return compare_face(known_filename_path,
                                video_path,
                                request_upload_folder_path,
                                request_frames_folder_path,
                                float(threshold))


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # add own IPV4 address for debug
    # In android, put android:usesCleartextTraffic="true" in manifest application tag
    server = make_server('192.168.0.161', 8080, middleware)
    server.serve_forever()
