# Face-Comparison

This is a Flask Web APP / API that able to compare face that found in image and video.


## Tech/Framework used [![js-standard-style](https://img.shields.io/badge/code%20style-standard-brightgreen.svg?style=flat)](https://github.com/feross/standard)
* [Face_Recognition python package](https://github.com/ageitgey/face_recognition) 
* Flask
* Gunicorn
* Opencv


## Installing on Unix or Windows
To run this project, install it locally using pip on a virtual environment by 
```sh
pip install -r requirements.txt
```


## Deployment
Deployment was done by using [Heroku](https://www.heroku.com/)  
Procfile is used to specifies the commands that are executed by the app on startup.  
You can try the web app that hosted [here](https://cardzone-face-matching.herokuapp.com/)


## Issues
There are some issues when trying to deploy this app on the web. Please see the link below for the fix. Some of the issues are
* dlib not able to install.
  * https://github.com/ageitgey/face_recognition/issues/3
* Additional buildpack / packages needed for installing OpenCV in VM.
  * https://elements.heroku.com/buildpacks/j-a-m-e-5/heroku16-buildpack-python-opencv-dlib
  * https://stackoverflow.com/questions/49469764/how-to-use-opencv-with-heroku/51004957

Aptfile

opencv-python-headless

## Authors
[**Lim Kha Shing**](https://www.linkedin.com/in/lim-kha-shing-836a24120/)
