import os
import face_recognition
import math

from flask import jsonify

from delete_files import delete_files
from video_processing import extract_frames_from_video
from constants import frames_folder


def face_distance_to_conf(face_distance, face_match_threshold=0.6):
    if face_distance > face_match_threshold:
        range_distance = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range_distance * 2.0)
        return linear_val
    else:
        range_distance = face_match_threshold
        linear_val = 1.0 - (face_distance / (range_distance * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))


def compare_face(known, video_name, threshold=0.6):
    extract_frames_from_video(video_name)

    # declare json key and default value pair
    face_found_in_image = False
    face_found_in_video = False
    final_confidence = 0
    confidences_list = []
    status_code = 404

    # Load the uploaded image file
    known_image = face_recognition.load_image_file(known)
    # face_encodings without [] is to get face encodings for any faces in the uploaded image
    known_face_encodings = face_recognition.face_encodings(known_image)

    known_face_encoding = []

    print("===== Face matching start =====")
    # if there is a face in known image
    if len(known_face_encodings) > 0:

        # since i know the image will always have 1 face, so only get the first face detected
        known_face_encoding = face_recognition.face_encodings(known_image)[0]
        face_found_in_image = True
        print("Found face in image")

    # loop through frames folder
    for i, frame in enumerate(os.listdir(frames_folder)):
        absolute_video_frame_directory_file = os.path.join(frames_folder, frame)

        unknown_image = face_recognition.load_image_file(absolute_video_frame_directory_file)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)

        # if extracted unknown frames have face,
        if len(unknown_face_encodings) > 0:
            face_found_in_video = True
            print("Found face in frame " + str(i))

            # if known image have face detected,
            # we proceed to compare it against unknown image
            if face_found_in_image:
                print("Proceed to compare face...")

                unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
                face_distances = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)

                confidence = face_distance_to_conf(face_distances, threshold)
                confidences_list.append(confidence[0])

    # average the final confidence value
    if face_found_in_video and face_found_in_video:
        status_code = 200
        final_confidence = sum(confidences_list) / float(len(confidences_list))
    else:
        print("Face not found in either video and image")

    print("===== Face comparison finished =====")

    # See if the first face in the uploaded image matches the known face
    # provide tolerance level to specify how strict it is. By default is 0.6
    # Uncomment below for use the API
    # match_results = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding, tolerance=0.6)

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

    delete_files()

    print(result)
    return jsonify(result)