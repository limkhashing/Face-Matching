# Face-Comparison 
[![Build Status](https://travis-ci.com/limkhashing/Face-Matching.svg?token=sZGsDojxrUtyz1ravQZ4&branch=master)](https://travis-ci.com/limkhashing/Face-Matching)
[![codecov](https://codecov.io/gh/limkhashing/Face-Matching/branch/master/graph/badge.svg?token=2WDJFB51rs)](https://codecov.io/gh/limkhashing/Face-Matching)
![Python Version](https://img.shields.io/pypi/pyversions/Django.svg)
![Side Project](https://img.shields.io/badge/Side-Project-yellowgreen.svg)
> This is a simple Python/Flask application that intended to compare face that found in an image and short video. It will return a JSON whether face found in image and video, a confidence percentage and whether is matched or not

## Tech/Framework used
* [Face_Recognition python package](https://github.com/ageitgey/face_recognition) 
* Flask
* Gunicorn
* OpenCV and FFMPEG

## Installing on Unix or Windows
To run this project, install it locally using pip on a virtual environment
```sh
pip install -r requirements.txt
```

## How does it work
1. Upload a picture of the person you want to compare
2. Upload a short video (mp4, avi, webm) 
3. Click compare and it will compare the face found in picture and video
   * Check the size of picture uploaded. If is above certain threshold, then it will be compress
   * Extract frame per second from video uploaded
     * Check the frame whether is rotated. If is rotated, rotate it back to portrait
   * Check the size of frame extracted. If is above certain threshold, then it will be compress
   * Loop through and comparing the picture and frames extracted. Confidence will be divided by how many frame counts
   
![flowchart](https://raw.githubusercontent.com/limkhashing/Face-Comparison/master/static/Face%20Matching%20Flowchart.jpg)

## Deployment
* Deployment was done by using [Heroku](https://www.heroku.com/)  
* Procfile is used to specifies the commands that are executed by the app on startup.  
* Aptfile is used to install additional software packages that application requires
* newrelic.ini is use for New Relic add-on for monitoring 

You can try the web app that hosted [here](https://matching-face.herokuapp.com/)

## Issues when deploying on Heroku / VM / Dockers
There are some issues when trying to deploy this app on the web. Please see the link below for the fix.  
Some of the issues are
* dlib not able to install.
  * https://github.com/ageitgey/face_recognition/issues/3
* Additional buildpack / Linux packages needed for installing OpenCV and FFMPEG in VM.
  * https://elements.heroku.com/buildpacks/j-a-m-e-5/heroku16-buildpack-python-opencv-dlib
  * https://elements.heroku.com/buildpacks/jonathanong/heroku-buildpack-ffmpeg-latest
  * https://elements.heroku.com/buildpacks/eventastic/heroku-buildpack-apt
  * https://stackoverflow.com/questions/49469764/how-to-use-opencv-with-heroku/51004957
  * https://stackoverflow.com/questions/47113029/importerror-libsm-so-6-cannot-open-shared-object-file-no-such-file-or-directo

## Authors
[**Lim Kha Shing**](https://www.linkedin.com/in/lim-kha-shing-836a24120/)
