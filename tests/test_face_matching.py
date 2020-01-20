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


# TODO write tests for flask endpoint, face matching and ocr
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

    def test_tolerance_and_threshold_default_value(self):
        self.tolerance = 0.50
        self.threshold = 0.80
        self.assertIsInstance(self.tolerance, float)
        self.assertIsInstance(self.threshold, float)

    def test_tolerance_and_threshold_specified_value(self):
        self.tolerance = '50'
        self.threshold = '80'
        self.tolerance = float(self.tolerance)
        self.threshold = float(self.threshold)
        self.assertIsInstance(self.tolerance, float)
        self.assertIsInstance(self.threshold, float)

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
