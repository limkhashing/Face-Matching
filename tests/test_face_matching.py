import io
import math
import os
import re
import unittest

import cv2
import pytesseract
from face_recognition import api
from flask import Flask

from app import app
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
        self.client = app.test_client()
        self.tolerance = ''
        self.threshold = ''

        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        # pytesseract.pytesseract.tesseract_cmd = r'D:/Tesseract-OCR/tesseract.exe'

    # executed after each test
    def tearDown(self):
        pass

    def test_base_route(self):
        url = '/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_route(self):
        url = '/api/upload'

        mock_image = os.path.join(test_data_path, 'my ic.jpg')
        mock_video = os.path.join(test_data_path, 'my video.mov')
        data = dict(
            known=(io.BytesIO(b"known"), mock_image),
            unknown=(io.BytesIO(b"unknown"), mock_video),
            tolerance=0.50,
            threshold=0.80,
            testing=True
        )

        response = self.client.post(url, content_type='multipart/form-data', data=data,
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_bad_route(self):
        url = '/api/upload'
        mock_image = os.path.join(test_data_path, 'my ic.jpg')
        data = dict(
            known=(io.BytesIO(b"known"), mock_image),
            tolerance=0.50,
            testing=True
        )

        response = self.client.post(url, content_type='multipart/form-data', data=data,
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_bad_api_request(self):
        url = '/route'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # OCR function
    @classmethod
    def process_ocr(self, image_path):
        IDENTITY_CARD = "IDENTITY CARD"
        DRIVING_LICENSE = "DRIVING LICENSE"
        PASSPORT = "PASSPORT"

        image_size = [600, 700, 800]
        regex_found = False

        for size in image_size:
            img = cv2.imread(image_path)
            img = cv2.resize(img, (size, size), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            ocr_result = pytesseract.image_to_string(img).upper()
            results = ocr_result.split()

            # check my ic
            for result in results:
                regex_found = re.search(IC_NUMBER_REGREX, result)
                if bool(regex_found):
                    break
            if (any(pattern in results for pattern in IC_PATTERNS) or bool(regex_found)) \
                    and not any(pattern in results for pattern in PASSPORT_PATTERNS):
                return IDENTITY_CARD, results

            # check driving, with regrex Date and IC Number
            for result in results:
                regex_found = re.search(DRIVING_DATE_REGREX, result)
                if bool(regex_found):
                    break

                regex_found = re.search(DRIVING_IC_NUMBER_REGREX, result)
                if bool(regex_found):
                    break
            if (any(pattern in results for pattern in DRIVING_PATTERN) or bool(regex_found)) \
                    and not any(pattern in results for pattern in PASSPORT_PATTERNS):
                return DRIVING_LICENSE, results

            # check passport
            for result in results:
                regex_found = re.search(PASSPORT_DATE_REGREX, result)
                if bool(regex_found):
                    break
            if any(pattern in results for pattern in PASSPORT_PATTERNS) or bool(regex_found):
                return PASSPORT, results
        return None, None

    def test_identity_card_ocr(self):
        ocr_result = self.process_ocr(os.path.join(test_data_path, 'identity card.jpg'))
        self.assertEqual(ocr_result[0], 'IDENTITY CARD')
        self.assertNotEqual(ocr_result[0], 'DRIVING LICENSE')
        self.assertNotEqual(ocr_result[0], 'PASSPORT')

    def test_driving_license_ocr(self):
        ocr_result = self.process_ocr(os.path.join(test_data_path, 'driving license.jpg'))
        self.assertEqual(ocr_result[0], 'DRIVING LICENSE')
        self.assertNotEqual(ocr_result[0], 'IDENTITY CARD')
        self.assertNotEqual(ocr_result[0], 'PASSPORT')

    def test_passport_ocr(self):
        ocr_result = self.process_ocr(os.path.join(test_data_path, 'passport.jpg'))
        self.assertEqual(ocr_result[0], 'PASSPORT')
        self.assertNotEqual(ocr_result[0], 'IDENTITY CARD')
        self.assertNotEqual(ocr_result[0], 'DRIVING LICENSE')

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
        ic_path = os.path.join(test_data_path, 'my ic.jpg')
        driving_license_path = os.path.join(test_data_path, 'my driving license.jpg')

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

        ic_path = os.path.join(test_data_path, 'my ic.jpg')
        driving_license_path = os.path.join(test_data_path, 'my driving license.jpg')

        image_ic = api.load_image_file(ic_path)
        image_driving_license = api.load_image_file(driving_license_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_driving = api.face_encodings(image_driving_license)[0]

        face_distances = api.face_distance([face_encoding_ic], face_encoding_driving)
        confidence = self.face_distance_to_conf(face_distances, self.tolerance)

        self.assertGreaterEqual(confidence, self.threshold)

    def test_bad_face_matching_confidence(self):
        self.tolerance = 0.50
        self.threshold = 0.80

        ic_path = os.path.join(test_data_path, 'my ic.jpg')
        passport_path = os.path.join(test_data_path, 'passport.jpg')

        image_ic = api.load_image_file(ic_path)
        image_passport = api.load_image_file(passport_path)

        face_encoding_ic = api.face_encodings(image_ic)[0]
        face_encoding_passport = api.face_encodings(image_passport)[0]

        face_distances = api.face_distance([face_encoding_ic], face_encoding_passport)
        confidence = self.face_distance_to_conf(face_distances, self.tolerance)

        self.assertLessEqual(confidence, self.threshold)
