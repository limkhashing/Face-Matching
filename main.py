# Reference
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py
# https://github.com/ageitgey/face_recognition/wiki/Calculating-Accuracy-as-a-Percentage
import glob
import math
import os
import cv2
import face_recognition

from flask import Flask, jsonify, request, redirect, render_template

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'webm'}
app = Flask(__name__)

# Constant variable for directory
app.config["FRAMES_FOLDER"] = "./frames"
app.config["VIDEO_FOLDER"] = "./video_upload"


def delete_files():
    for file in os.listdir(app.config["FRAMES_FOLDER"]):
        file_path = os.path.join(app.config["FRAMES_FOLDER"] , file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    for file in os.listdir(app.config["VIDEO_FOLDER"]):
        file_path = os.path.join(app.config["VIDEO_FOLDER"] , file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def face_distance_to_conf(face_distance, face_match_threshold=0.6):
    if face_distance > face_match_threshold:
        range = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range * 2.0)
        return linear_val
    else:
        range = face_match_threshold
        linear_val = 1.0 - (face_distance / (range * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))


def extract_frames_from_video(video_name):
    count = 1
    video = os.path.join(app.config["VIDEO_FOLDER"], video_name)
    vidcap = cv2.VideoCapture(video)
    while True:
        # 1000 for 1 seconds
        vidcap.set(cv2.CAP_PROP_POS_MSEC, (count * 1000))
        success, image = vidcap.read()
        if not success:
            break
        print('Read a new frame: ', success)
        cv2.imwrite(os.path.join(app.config["FRAMES_FOLDER"], "frame%d.jpg") % count, image) # save frame as JPEG file
        count = count + 1


def face_comparison(original, video_name):
    extract_frames_from_video(video_name)

    # declare json key and default value pair
    face_found_in_image = False
    face_found_in_video = False
    final_confidence = 0

    # Load the uploaded image file
    original_image = face_recognition.load_image_file(original)
    # face_encodings without [] is to get face encodings for any faces in the uploaded image
    original_face_encodings = face_recognition.face_encodings(original_image)

    # variable count to average out how many frames extracted
    count = 0

    # if there is a face in original image
    if(len(original_face_encodings) > 0):

        # since i know the image will always have 1 face, so only get the first face detected
        original_face_encoding = face_recognition.face_encodings(original_image)[0]
        face_found_in_image = True

        # loop through frames folder
        for frame in os.listdir(app.config["FRAMES_FOLDER"]):
            absoulute_video_frame_directory_file = os.path.join(app.config["FRAMES_FOLDER"], frame)

            unknown_image = face_recognition.load_image_file(absoulute_video_frame_directory_file)
            unknown_face_encodings = face_recognition.face_encodings(unknown_image)

            # if extracted unknown frames have face, we proceed to compare it against original
            if len(unknown_face_encodings) > 0:
                unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
                face_found_in_video = True

                # get the confidence rate
                face_distances = face_recognition.face_distance([original_face_encoding], unknown_face_encoding)
                confidence = face_distance_to_conf(face_distances)
                final_confidence = final_confidence + confidence[0]
                count = count + 1

    # average the final confidence value
    final_confidence = final_confidence / count
    print("Final Confidence = ", final_confidence)

    # See if the first face in the uploaded image matches the known face
    # provide tolerance level to specify how strict it is. By default is 0.6
    # Uncomment below for use the API
    # match_results = face_recognition.compare_faces([original_face_encoding], unknown_face_encoding, tolerance=0.6)

    if final_confidence > 0.6:
        is_match = True
    else:
        is_match = False

    # Return the result as json
    result = {
        "face_found_in_image": face_found_in_image,
        "face_found_in_video": face_found_in_video,
        "is_match": is_match,
        "confidence": final_confidence
    }
    delete_files()
    return jsonify(result)


@app.route('/api/upload', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image and video file was uploaded
    if request.method == 'POST':
        if 'original' not in request.files:
            return redirect(request.url)

        if 'unknown' not in request.files:
            return redirect(request.url)

        original = request.files['original']
        unknown = request.files['unknown']

        if original.filename == '':
            return redirect(request.url)

        if unknown.filename == '':
            return redirect(request.url)

        # Check if folder existed or not. If not then create it
        if not os.path.exists(app.config["VIDEO_FOLDER"]):
            os.makedirs(app.config["VIDEO_FOLDER"])
        if not os.path.exists(app.config["FRAMES_FOLDER"]):
            os.makedirs(app.config["FRAMES_FOLDER"])

        unknown.save(os.path.join(app.config["VIDEO_FOLDER"], unknown.filename))

        if original and allowed_file(original.filename) and unknown and allowed_file(unknown.filename):
            return face_comparison(original, unknown.filename)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)