import math
import re
import unittest
import os
import cv2
import ffmpeg
import pytesseract

from face_recognition import api
from flask import Flask

from src.app import app
from tests.regex_patterns import IC_NUMBER_REGREX, IC_PATTERNS, DRIVING_DATE_REGREX, DRIVING_IC_NUMBER_REGREX, \
    DRIVING_PATTERN, PASSPORT_DATE_REGREX, PASSPORT_PATTERNS

test_data_path = os.path.join(os.path.dirname(__file__), 'test_data')
test_frames_path = os.path.join(os.path.dirname(__file__), 'test_frames')
image_size_threshold = 500000
frame_size_threshold = 200000


class TestFaceMatching(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True

        template_dir = os.path.abspath('../templates')
        static = os.path.abspath('../static')
        self.app = Flask(__name__, template_folder=template_dir, static_url_path='', static_folder=static)
        self.app = app.test_client()
        self.tolerance = ''
        self.threshold = ''

    # executed after each test
    def tearDown(self):
        pass

    def test_tolerance_and_threshold_value(self):
        # test default tolerance and threshold value
        if self.tolerance != '':
            self.tolerance = float(self.tolerance)
        else:
            self.tolerance = 0.50

        if self.threshold != '':
            self.threshold = float(self.threshold)
        else:
            self.threshold = 0.80
        self.assertIsInstance(self.tolerance, float)
        self.assertIsInstance(self.threshold, float)

        # test tolerance and threshold specified value
        self.tolerance = '50'
        self.threshold = '80'
        if self.tolerance != '':
            self.tolerance = float(self.tolerance)
        else:
            self.tolerance = 0.50

        if self.threshold != '':
            self.threshold = float(self.threshold)
        else:
            self.threshold = 0.80
        self.assertIsInstance(self.tolerance, float)
        self.assertIsInstance(self.threshold, float)

    # fail the upload post request since i dont want to upload any file for testing
    # it will return http code 400 - bad request
    def upload(self):
        return self.app.post(
            '/api/upload',
            content_type='multipart/form-data',
            data=dict(
                tolerance=0.50,
                threshold=0.80
            ),
            follow_redirects=True
        )

    def test_post(self):
        response = self.upload()
        self.assertEqual(response.status_code, 400)

    # test extract frame from video
    @classmethod
    def check_rotation(cls, path_video_file):
        print("Checking orientation of video received")

        meta_dict = ffmpeg.probe(path_video_file)
        rotateCode = None
        rotate_angle = ''

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
                    rotate_angle = 'NO_ROTATE'
        print("Rotated to = ", rotate_angle)
        return rotateCode

    @classmethod
    def correct_rotation(cls, frame, rotateCode):
        return cv2.rotate(frame, rotateCode)

    def test_extract_frames_from_video(self):
        for filename in os.listdir(test_data_path):
            if filename.endswith(".mov") or filename.endswith(".mp4"):
                video_path = os.path.join(test_data_path, filename)
                count = 0

                rotate_code = self.check_rotation(video_path)

                cap = cv2.VideoCapture(video_path)
                frame_rate = cap.get(5)

                while cap.isOpened():
                    frame_id = cap.get(1)
                    ret, frame = cap.read()
                    if ret:
                        if rotate_code is not None:
                            frame = self.correct_rotation(frame, rotate_code)

                        if frame_id % math.floor(frame_rate) == 0:
                            self.assertTrue(cv2.imwrite(test_frames_path + '/frame_%d.jpg' % count, frame))

                            frame_size = os.stat(test_frames_path + '/frame_%d.jpg' % count).st_size

                            if frame_size > frame_size_threshold:
                                frame = cv2.resize(frame, None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
                                self.assertTrue(cv2.imwrite(test_frames_path + '/frame_%d.jpg' % count, frame))
                            count = count + 1
                    else:
                        break

                cap.release()

    def test_resize_image(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        known_image_size = os.stat(ic_path).st_size
        if known_image_size > image_size_threshold:
            known_image = cv2.imread(ic_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
            self.assertTrue(cv2.imwrite(ic_path, resized_image))

        known_image_size = os.stat(driving_license_path).st_size
        if known_image_size > image_size_threshold:
            known_image = cv2.imread(driving_license_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1)
            self.assertTrue(cv2.imwrite(driving_license_path, resized_image))

    def test_classify_ID_images(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')
        passport_path = os.path.join(test_data_path, 'passport.jpg')

        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

        IDENTITY_CARD = "IDENTITY CARD"
        DRIVING_LICENSE = "DRIVING LICENSE"
        PASSPORT = "PASSPORT"

        image_size = [600, 700, 800]
        image_list = [ic_path, driving_license_path, passport_path]
        regex_found = False
        doc_type = None

        for image in image_list:
            for size in image_size:
                img = cv2.imread(image)
                img = cv2.resize(img, (size, size), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

                ocr_result = pytesseract.image_to_string(img).upper()
                results = ocr_result.split()

                # check ic
                for result in results:
                    regex_found = re.search(IC_NUMBER_REGREX, result)
                    if bool(regex_found):
                        break
                if any(pattern in results for pattern in IC_PATTERNS) or bool(regex_found):
                    doc_type = IDENTITY_CARD

                # check driving, with regrex Date and IC Number
                for result in results:
                    regex_found = re.search(DRIVING_DATE_REGREX, result)
                    if bool(regex_found):
                        break
                    regex_found = re.search(DRIVING_IC_NUMBER_REGREX, result)
                    if bool(regex_found):
                        break
                if any(pattern in results for pattern in DRIVING_PATTERN) or bool(regex_found):
                    doc_type = DRIVING_LICENSE

                # check passport
                for result in results:
                    regex_found = re.search(PASSPORT_DATE_REGREX, result)
                    if bool(regex_found):
                        break
                if any(pattern in results for pattern in PASSPORT_PATTERNS) or bool(regex_found):
                    doc_type = PASSPORT

            if image is ic_path:
                self.assertIs(doc_type, IDENTITY_CARD)
            if image is driving_license_path:
                self.assertIs(doc_type, DRIVING_LICENSE)
            if image is passport_path:
                self.assertIs(doc_type, PASSPORT)

    def test_delete_files(self):
        for frame in os.listdir(test_frames_path):
            file_path = os.path.join(test_frames_path, frame)
            try:
                if os.path.isfile(file_path):
                    self.assertIsNone(os.unlink(file_path))
            except Exception as e:
                print(e)

    #  test face matching functions
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

    def test_face_matching(self):
        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        image_ic = api.load_image_file(ic_path)
        image_driving_license = api.load_image_file(driving_license_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_driving = api.face_encodings(image_driving_license)[0]

        self.tolerance = 0.50
        match_results = api.compare_faces([face_encoding_ic], face_encoding_driving, tolerance=self.tolerance)

        self.assertEqual(type(match_results), list)
        self.assertTrue(match_results[0])

    def test_face_matching_confidence(self):
        self.tolerance = 0.50
        self.threshold = 0.80

        ic_path = os.path.join(test_data_path, 'IC.jpg')
        driving_license_path = os.path.join(test_data_path, 'driving license.jpg')

        image_ic = api.load_image_file(ic_path)
        image_driving_license = api.load_image_file(driving_license_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_driving = api.face_encodings(image_driving_license)[0]

        face_distances = api.face_distance([face_encoding_ic], face_encoding_driving)
        confidence = self.face_distance_to_conf(face_distances, self.tolerance)

        self.assertGreaterEqual(confidence, self.threshold)