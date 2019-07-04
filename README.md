# Face-Comparison

This is a Flask Web APP / API that able to compare face that found in image and video.


## Tech/Framework used
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
They're bound to have issues when using this app on the web. 
Some of the issue is
* dlib not able to install. Please see the link below for fix
* Opencv 
* you can use a buildpack to install apt libs.

https://github.com/ageitgey/face_recognition/issues/3
https://elements.heroku.com/buildpacks/j-a-m-e-5/heroku16-buildpack-python-opencv-dlib
https://github.com/jeromevonk/flask_face_detection

aptfile
dlib
opencv-python-headless

## Authors
[**Lim Kha Shing**](https://www.linkedin.com/in/lim-kha-shing-836a24120/)
