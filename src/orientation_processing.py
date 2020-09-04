# Remember to put FFMPEG in variable path

import math
import os

import cv2
import ffmpeg

from src.constants import frame_size_threshold


def check_rotation(path_video_file):
    # Start checking orientation of video received
    print("Checking orientation of video received")

    # this returns meta-data of the video file in form of a dictionary
    meta_dict = ffmpeg.probe(path_video_file)

    # from the dictionary, meta_dict['streams'][0]['tags']['rotate'] is the key we are looking for
    rotate_code = None
    rotate_angle = 'NO_ROTATE'

    # try rotate the image by finding rotate key meta_dict
    # if no, prompt message and skip
    for stream in meta_dict['streams']:
        if 'rotate' in stream['tags']:
            if int(stream['tags']['rotate']) == 90:
                rotate_code = cv2.ROTATE_90_CLOCKWISE
                rotate_angle = 'ROTATE_90_CLOCKWISE'
            elif int(stream['tags']['rotate']) == 180:
                rotate_code = cv2.ROTATE_180
                rotate_angle = 'ROTATE_180'
            elif int(stream['tags']['rotate']) == 270:
                rotate_code = cv2.ROTATE_90_COUNTERCLOCKWISE
                rotate_angle = 'ROTATE_90_COUNTERCLOCKWISE'
            else:
                print("No rotation metadata. Skip check rotation")

    print("Rotated to = ", rotate_angle)
    return rotate_code


def correct_rotation(frame, rotate_code):
    return cv2.rotate(frame, rotate_code)


def extract_frames_from_video(video_path, request_frames_folder_path):
    count = 0

    # check if video requires rotation
    rotate_code = check_rotation(video_path)

    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(5)  # frame rate

    while cap.isOpened():
        frame_id = cap.get(1)  # current frame number
        ret, frame = cap.read()
        if ret:

            # check rotate_code
            # If got code, rotate the frame back to original orientation
            if rotate_code is not None:
                frame = correct_rotation(frame, rotate_code)

            if frame_id % math.floor(frame_rate) == 0:
                print('Extract the new %d frame of video...' % count)
                cv2.imwrite(request_frames_folder_path + '/frame_%d.jpg' % count, frame)

                # check extracted frame size is large than
                frame_size = os.stat(request_frames_folder_path + '/frame_%d.jpg' % count).st_size

                if frame_size > frame_size_threshold:
                    print('Resizing the new %d frame of video...' % count)
                    frame = cv2.resize(frame, None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
                    cv2.imwrite(request_frames_folder_path + '/frame_%d.jpg' % count, frame)

                count = count + 1
        else:
            break

    cap.release()
