import math
import unittest
import os
import cv2
import ffmpeg

from face_recognition import api
from app import app

test_data_path = os.path.join(os.path.dirname(__file__), 'test_data')
test_frames_path = os.path.join(os.path.dirname(__file__), 'test_frames')
image_size_threshold = 500000
frame_size_threshold = 200000
tolerance = 0.5
threshold = 0.80


class TestFaceMatching(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    # executed after each test
    def tearDown(self):
        pass

    # test flask endpoint
    def test_home_status_code(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    # test extract frame from video
    @classmethod
    def check_rotation(cls, path_video_file):
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

        for stream in meta_dict['streams']:
            if 'rotate' in stream['tags']:
                if int(stream['tags']['rotate']) == 90:
                    rotateCode = cv2.ROTATE_90_CLOCKWISE
                    rotate_angle = 'ROTATE_90_CLOCKWISE'
                elif int(stream['tags']['rotate']) == 180:
                    rotateCode = cv2.ROTATE_180
                    rotate_angle = 'ROTATE_180'
                elif int(stream['tags']['rotate']) == 270:
                    rotateCode = cv2.ROTATE_90_COUNTERCLOCKWISE
                    rotate_angle = 'ROTATE_90_COUNTERCLOCKWISE'
                else:
                    print("No rotation metadata. Skip check rotation")

        print("Rotated to = ", rotate_angle)
        return rotateCode

    @classmethod
    def correct_rotation(cls, frame, rotateCode):
        return cv2.rotate(frame, rotateCode)

    @classmethod
    def create_test_frames_directory(cls):
        if not os.path.exists(test_frames_path):
            os.makedirs(test_frames_path)

    def test_extract_frames_from_video(self):

        self.create_test_frames_directory()

        for filename in os.listdir(test_data_path):
            if filename.endswith(".mov") or filename.endswith(".mp4"):
                video_path = os.path.join(test_data_path, filename)
                count = 0

                # check if video requires rotation
                rotate_code = self.check_rotation(video_path)

                cap = cv2.VideoCapture(video_path)
                frame_rate = cap.get(5)  # frame rate

                while cap.isOpened():
                    frame_id = cap.get(1)  # current frame number
                    ret, frame = cap.read()
                    if ret == True:
                        # check rotate_code.
                        # If got code, rotate the frame back to original orientation
                        if rotate_code is not None:
                            frame = self.correct_rotation(frame, rotate_code)

                        if frame_id % math.floor(frame_rate) == 0:
                            print('Extract the new %d frame of video...' % count)
                            assert cv2.imwrite(test_frames_path + '/frame_%d.jpg' % count, frame)

                            # check extracted frame size is large than
                            frame_size = os.stat(test_frames_path + '/frame_%d.jpg' % count).st_size

                            if frame_size > frame_size_threshold:
                                print('Resizing the new %d frame of video...' % count)
                                frame = cv2.resize(frame, None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
                                assert cv2.imwrite(test_frames_path + '/frame_%d.jpg' % count, frame)

                            count = count + 1
                    else:
                        break

                cap.release()
                self.test_delete_files()

    def test_delete_files(self):
        for frame in os.listdir(test_frames_path):
            file_path = os.path.join(test_frames_path, frame)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    @classmethod
    def face_distance_to_conf(cls, face_distance, face_match_threshold=0.5):
        if face_distance > face_match_threshold:
            range_distance = (1.0 - face_match_threshold)
            linear_val = (1.0 - face_distance) / (range_distance * 2.0)
            return linear_val
        else:
            range_distance = face_match_threshold
            linear_val = 1.0 - (face_distance / (range_distance * 2.0))
            return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))

    def test_resize_image(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        known_image_size = os.stat(ic_path).st_size
        if known_image_size > image_size_threshold:
            known_image = cv2.imread(ic_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
            assert cv2.imwrite(ic_path, resized_image)

        known_image_size = os.stat(driving_license_path).st_size
        if known_image_size > image_size_threshold:
            known_image = cv2.imread(driving_license_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
            assert cv2.imwrite(driving_license_path, resized_image)

    def test_face_matching(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        image_ic = api.load_image_file(ic_path)
        image_driving_license = api.load_image_file(driving_license_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_driving = api.face_encodings(image_driving_license)[0]

        match_results = api.compare_faces([face_encoding_ic], face_encoding_driving, tolerance=tolerance)

        self.assertEqual(type(match_results), list)
        self.assertTrue(match_results[0])

    def test_face_matching_confidence(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        image_ic = api.load_image_file(ic_path)
        image_driving_license = api.load_image_file(driving_license_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_driving = api.face_encodings(image_driving_license)[0]

        face_distances = api.face_distance([face_encoding_ic], face_encoding_driving)
        confidence = self.face_distance_to_conf(face_distances, tolerance)

        self.assertGreaterEqual(confidence, threshold)
