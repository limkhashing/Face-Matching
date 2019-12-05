import os
import face_recognition
import math

from flask import jsonify

from src.OCR.process_ocr import process_ocr
from src.delete_files import delete_files
from src.orientation_processing import extract_frames_from_video


# https://github.com/ageitgey/face_recognition/wiki/Calculating-Accuracy-as-a-Percentage
def face_distance_to_conf(face_distance, face_match_threshold=0.5):
    if face_distance > face_match_threshold:
        range_distance = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range_distance * 2.0)
        return linear_val
    else:
        range_distance = face_match_threshold
        linear_val = 1.0 - (face_distance / (range_distance * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))


def compare_face(known, video_path, request_upload_folder_path, request_frames_folder_path,
                 tolerance, threshold):

    # declare json key and default value pair
    face_found_in_image = False
    face_found_in_video = False
    final_confidence = None
    is_match = None
    confidences_list = []
    known_face_encoding = []

    # Load the uploaded image file
    known_image = face_recognition.load_image_file(known)
    # face_encodings without [] is to get face encodings for any faces in the uploaded image
    known_face_encodings = face_recognition.face_encodings(known_image)

    #####
    # Part 1: Check whether there is a face in known image
    #####
    if len(known_face_encodings) > 0:
        # since i know the image will always have 1 face, so only get the first face detected
        known_face_encoding = face_recognition.face_encodings(known_image)[0]
        face_found_in_image = True
        print("Found face in image")

    #####
    # Part 2: Extract frames from video
    # Then Loop through request frame folder and check whether there is a face
    # if there is at least 1 face, we set to true and break
    #####
    extract_frames_from_video(video_path, request_frames_folder_path)

    for i, frame in enumerate(os.listdir(request_frames_folder_path)):
        absolute_video_frame_directory_file = os.path.join(request_frames_folder_path, frame)
        unknown_image = face_recognition.load_image_file(absolute_video_frame_directory_file)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)
        if len(unknown_face_encodings) > 0:
            face_found_in_video = True
            print("There is at least one face in frame. Continue matching the face")
            break

    #####
    # Part 3: Perform face matching with image and video
    # After compared with the face in image with each frame
    # It will automatically delete the uploaded data and frames extracted
    #####
    if face_found_in_video and face_found_in_image:
        print("=============== Face matching start ===============")
        # loop through request folder for each frame
        for i, frame in enumerate(os.listdir(request_frames_folder_path)):
            absolute_video_frame_directory_file = os.path.join(request_frames_folder_path, frame)
            unknown_image = face_recognition.load_image_file(absolute_video_frame_directory_file)
            unknown_face_encodings = face_recognition.face_encodings(unknown_image)

            # if extracted unknown frames have face,
            if len(unknown_face_encodings) > 0:
                print("Matching the face in frame %d..." % i)
                unknown_face_encoding = face_recognition.face_encodings(unknown_image, num_jitters=1)[0]
                face_distances = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)
                confidence = face_distance_to_conf(face_distances, tolerance)
                confidences_list.append(confidence[0])

                # See if the first face in the uploaded image matches the known face
                # provide tolerance level to specify how strict it is. By default is 0.5
                # Uncomment below for use the API
                # match_results = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding,
                #                                                tolerance=tolerance)
                # print(match_results)
    else:
        print("Did not found face in either image or video. Can't proceed to compare with image")
        file_type = process_ocr(known)
        delete_files(request_upload_folder_path, request_frames_folder_path)
        return jsonify(get_json_response(face_found_in_image, face_found_in_video, is_match, final_confidence, file_type))

    #####
    # Part 4: Check whether confidence > threshold
    # and return the result as Json
    #####
    final_confidence = sum(confidences_list) / float(len(confidences_list))
    if final_confidence >= threshold:
        is_match = True
    else:
        is_match = False

    print("=============== Face Matching Successful ===============")

    file_type = process_ocr(known)

    delete_files(request_upload_folder_path, request_frames_folder_path)

    return jsonify(get_json_response(face_found_in_image, face_found_in_video, is_match, final_confidence, file_type))


def get_json_response(face_found_in_image, face_found_in_video, is_match, final_confidence, file_type):
    return {
        "face_found_in_image": face_found_in_image,
        "face_found_in_video": face_found_in_video,
        "is_match": is_match,
        "confidence": final_confidence,
        "file_type": file_type
    }