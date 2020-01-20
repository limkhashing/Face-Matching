# Author: Lim Kha Shing
# Reference
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py

import os

import cv2
import request_id
from flask import Flask, jsonify, request, render_template
from request_id import RequestIdMiddleware
from werkzeug.serving import make_server

from src.OCR.crop_morphology import crop_morphology
from src.constants import ALLOWED__PICTURE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, frames_folder, upload_folder, \
    image_size_threshold, max_resize
from src.face_processing import compare_face

template_dir = os.path.abspath('templates')
static = os.path.abspath('static')
app = Flask(__name__, template_folder=template_dir, static_url_path='', static_folder=static)

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


def create_directories():
    # Check if upload and frames folder existed or not.
    # If not then create it
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)

    # Get unique Request ID
    face_matching_request_id = request_id.get_request_id(request)
    print("Request ID:", face_matching_request_id)

    # create a subdirectory with unique request id inside frames and upload folder
    request_upload_folder_path = os.path.join(upload_folder, face_matching_request_id)
    request_frames_folder_path = os.path.join(frames_folder, face_matching_request_id)
    os.makedirs(request_frames_folder_path)
    os.makedirs(request_upload_folder_path)

    return request_upload_folder_path, request_frames_folder_path


def set_tolerance_and_threshold(tolerance, threshold):
    if tolerance != '':
        tolerance = float(tolerance)
    else:
        tolerance = 0.50

    if threshold != '':
        threshold = float(threshold)
    else:
        threshold = 0.80

    print("Tolerance: ", tolerance)
    print("Threshold: ", threshold)

    return tolerance, threshold


@app.route('/api/upload', methods=['POST'])
def upload_image_video():

    # Check whether files is uploaded or not
    if request.files['known'].filename == '':
        print("no files in known")
        return get_error_result("Image", True)
    if request.files['unknown'].filename == '':
        print("no files in unknown")
        return get_error_result("Video", True)

    # Check if a valid image and video file was uploaded
    known = request.files['known']
    unknown = request.files['unknown']

    # Flask doesn't receive any information about
    # what type the client intended each value to be.
    # So it parses all values as strings.
    # And we need to parse it manually to float and set the value
    tolerance = request.form['tolerance']
    threshold = request.form['threshold']
    tolerance, threshold = set_tolerance_and_threshold(tolerance, threshold)

    if not known.filename.lower().endswith(ALLOWED__PICTURE_EXTENSIONS):
        print(known.filename)
        return get_error_result("Image", False)
    if not unknown.filename.lower().endswith(ALLOWED_VIDEO_EXTENSIONS):
        print(unknown.filename)
        return get_error_result("Video", False)

    request_upload_folder_path, request_frames_folder_path = create_directories()

    # create absolutely paths for the uploaded files
    unknown_filename_path = os.path.join(request_upload_folder_path, unknown.filename)
    known_filename_path = os.path.join(request_upload_folder_path, known.filename)

    # Save the uploaded files to directory
    # Example: upload/request-id/image.jpg
    unknown.save(unknown_filename_path)
    known.save(known_filename_path)

    video_path = os.path.join(request_upload_folder_path, unknown.filename)

    if known and unknown:

        # Resize the known image and scale it down
        known_image_size = os.stat(known_filename_path).st_size
        print("Image Size: ", known_image_size)
        if known_image_size > image_size_threshold:
            print("Resizing the known image as it was larger than ", image_size_threshold)
            known_image = cv2.imread(known_filename_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
            cv2.imwrite(known_filename_path, resized_image)
            print("Resized image ", os.stat(known_filename_path).st_size)

            if os.stat(known_filename_path).st_size < max_resize:
                print("Enlarge back as it smaller than ", max_resize)
                known_image = cv2.imread(known_filename_path)
                resized_image = cv2.resize(known_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(known_filename_path, resized_image)
                print("Resized image ", os.stat(known_filename_path).st_size)

        crop_morphology(known_filename_path)

        # process both image and video
        return compare_face(known_filename_path,
                            video_path,
                            request_upload_folder_path,
                            request_frames_folder_path,
                            tolerance=tolerance,
                            threshold=threshold)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # add own IPV4 address for debug
    # In android, put android:usesCleartextTraffic="true" in manifest application tag
    # for allow cross domain to LocalHost
    server = make_server('0.0.0.0', 8080, middleware)
    server.serve_forever()
