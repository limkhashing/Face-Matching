# Author: Lim Kha Shing
# Reference
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py
# https://github.com/ageitgey/face_recognition/wiki/Calculating-Accuracy-as-a-Percentage

import os
import cv2
import face_recognition
import ffmpeg
import math
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from rq import Queue
from worker import conn

# You can change this to any folder on your system
ALLOWED__PICTURE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')
ALLOWED_VIDEO_EXTENSIONS = ('mp4', 'avi', 'webm', 'mov')

app = Flask(__name__)
q = Queue(connection=conn)

# Constant variable for directory
app.config["FRAMES_FOLDER"] = "./frames"
app.config["UPLOAD_FOLDER"] = "./upload"

def test_compare(unknown_image):
    unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
    return unknown_face_encoding


def get_status(job):
    status = {
        'id': job.id,
        'result': job.result,
        'status': 'failed' if job.is_failed else 'pending' if job.result == None else 'completed'
    }
    status.update(job.meta)
    return status


def delete_files():
    for file in os.listdir(app.config["FRAMES_FOLDER"]):
        file_path = os.path.join(app.config["FRAMES_FOLDER"], file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    for file in os.listdir(app.config["UPLOAD_FOLDER"]):
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def face_distance_to_conf(face_distance, face_match_threshold=0.6):
    if face_distance > face_match_threshold:
        range_distance = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range_distance * 2.0)
        return linear_val
    else:
        range_distance = face_match_threshold
        linear_val = 1.0 - (face_distance / (range_distance * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))


def check_rotation(path_video_file):
    # Start checking orientation of video received
    print("Checking orientation of video received")

    # this returns meta-data of the video file in form of a dictionary
    meta_dict = ffmpeg.probe(path_video_file)

    # from the dictionary, meta_dict['streams'][0]['tags']['rotate'] is the key
    # we are looking for
    rotateCode = None
    rotate_angle = 'NO_ROTATE'

    # try rotate the image by finding rotate key meta_dict
    # if no, prompt message
    try:
        if int(meta_dict['streams'][0]['tags']['rotate']) == 90:
            rotateCode = cv2.ROTATE_90_CLOCKWISE
            rotate_angle = 'ROTATE_90_CLOCKWISE'
        elif int(meta_dict['streams'][0]['tags']['rotate']) == 180:
            rotateCode = cv2.ROTATE_180
            rotate_angle = 'ROTATE_180'
        elif int(meta_dict['streams'][0]['tags']['rotate']) == 270:
            rotateCode = cv2.ROTATE_90_COUNTERCLOCKWISE
            rotate_angle = 'ROTATE_90_COUNTERCLOCKWISE'
    except KeyError:
        print("No rotation metadata. Skip check rotation")

    print("Rotated to = ", rotate_angle)
    return rotateCode


def correct_rotation(frame, rotateCode):
    return cv2.rotate(frame, rotateCode)


def extract_frames_from_video(video_name):
    count = 0
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], video_name)

    # TODO uncomment this to allow rotate
    # check if video requires rotation
    rotate_code = check_rotation(video_path)

    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(5)  # frame rate

    while cap.isOpened():
        frame_id = cap.get(1)  # current frame number
        ret, frame = cap.read()
        if ret == True:

            # TODO uncomment this to allow rotate
            if rotate_code is not None:
                frame = correct_rotation(frame, rotate_code)

            if frame_id % math.floor(frame_rate) == 0:
                print('Writing a new %d frame of video...' % count)
                cv2.imwrite("./frames/frame_%d.jpg" % count, frame)
                count = count + 1
        else:
            break

    cap.release()


def face_comparison(original, video_name, threshold=0.6):
    extract_frames_from_video(video_name)

    # declare json key and default value pair
    face_found_in_image = False
    face_found_in_video = False
    final_confidence = 0
    status_code = 404

    # Load the uploaded image file
    original_image = face_recognition.load_image_file(original)
    # face_encodings without [] is to get face encodings for any faces in the uploaded image
    original_face_encodings = face_recognition.face_encodings(original_image)

    # variable count to average out how many frames extracted
    count = 0

    original_face_encoding = []

    print("===== Face matching start =====")
    # if there is a face in original image
    if len(original_face_encodings) > 0:

        # since i know the image will always have 1 face, so only get the first face detected
        original_face_encoding = face_recognition.face_encodings(original_image)[0]
        face_found_in_image = True
        print("Found face in image")

    # loop through frames folder
    for i, frame in enumerate(os.listdir(app.config["FRAMES_FOLDER"])):
        absolute_video_frame_directory_file = os.path.join(app.config["FRAMES_FOLDER"], frame)

        unknown_image = face_recognition.load_image_file(absolute_video_frame_directory_file)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)

        # if extracted unknown frames have face,
        if len(unknown_face_encodings) > 0:
            face_found_in_video = True
            print("Found face in frame " + str(i))

            # if original image have face detected,
            # we proceed to compare it against unknown image
            if face_found_in_image:
                print("Proceed to compare face...")

                unknown_face_encoding = q.enqueue(test_compare, unknown_image)
                # unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
                face_distances = face_recognition.face_distance([original_face_encoding], unknown_face_encoding)

                confidence = face_distance_to_conf(face_distances, threshold)
                final_confidence = final_confidence + confidence[0]
                count = count + 1

    # average the final confidence value
    if face_found_in_video and face_found_in_video:
        if count is not 0:
            status_code = 200
            final_confidence = final_confidence / count
    else:
        print("Face not found in either video and image")

    print("===== Face comparison finished =====")

    # See if the first face in the uploaded image matches the known face
    # provide tolerance level to specify how strict it is. By default is 0.6
    # Uncomment below for use the API
    # match_results = face_recognition.compare_faces([original_face_encoding], unknown_face_encoding, tolerance=0.6)

    if final_confidence > threshold:
        is_match = True
    else:
        is_match = False

    # Return the result as json
    result = {
        "status_code": status_code,
        "face_found_in_image": face_found_in_image,
        "face_found_in_video": face_found_in_video,
        "is_match": is_match,
        "confidence": final_confidence
    }

    # delete_files()

    print(result)
    return jsonify(result)


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


@app.route('/api/upload', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image and video file was uploaded
    if request.method == 'POST':

        if request.files['original'].filename == '':
            print("no files in original")
            return get_error_result("Image", True)

        if request.files['unknown'].filename == '':
            print("no files in unknown")
            return get_error_result("Video", True)

        original = request.files['original']
        unknown = request.files['unknown']
        threshold = request.form['threshold']

        if not original.filename.lower().endswith(ALLOWED__PICTURE_EXTENSIONS):
            print(original.filename)
            return get_error_result("Image", False)

        if not unknown.filename.lower().endswith(ALLOWED_VIDEO_EXTENSIONS):
            print(unknown.filename)
            return get_error_result("Video", False)

        # Check if folder existed or not. If not then create it
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])
        if not os.path.exists(app.config["FRAMES_FOLDER"]):
            os.makedirs(app.config["FRAMES_FOLDER"])

        unknown_filename = secure_filename(unknown.filename)

        unknown.save(os.path.join(app.config["UPLOAD_FOLDER"], unknown_filename))
        original.save(os.path.join(app.config["UPLOAD_FOLDER"], original.filename))

        if original and unknown:

            # TODO Resize the image and scale it down
            image_size = os.stat(os.path.join(app.config["UPLOAD_FOLDER"], original.filename)).st_size
            print("Image Size: ", image_size)
            if image_size > 500000:
                print("Resize the image")
                original_image = cv2.imread(os.path.join(app.config["UPLOAD_FOLDER"], original.filename))
                resized_image = cv2.resize(original_image, None, fx=0.07, fy=0.07)
                cv2.imwrite(os.path.join(app.config["UPLOAD_FOLDER"], original.filename), resized_image)

            if threshold == '':
                print("Threshold is blank. Use default 0.6")
                return face_comparison(os.path.join(app.config["UPLOAD_FOLDER"], original.filename), unknown_filename)
            print("Threshold is specified. Use " + threshold)
            return face_comparison(os.path.join(app.config["UPLOAD_FOLDER"], original.filename), unknown_filename, float(threshold))


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
