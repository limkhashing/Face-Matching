# Face Matching
[![Build Status](https://travis-ci.com/limkhashing/Face-Matching.svg?token=sZGsDojxrUtyz1ravQZ4&branch=master)](https://travis-ci.com/limkhashing/Face-Matching)
[![codecov](https://codecov.io/gh/limkhashing/Face-Matching/branch/master/graph/badge.svg?token=2WDJFB51rs)](https://codecov.io/gh/limkhashing/Face-Matching)
> This is a simple Python/Flask application that intended to compare face that found in an image and short video. It will return a JSON whether face found in image and video, a confidence percentage and whether is matched or not

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

## Tech/Framework used
* [Face_Recognition python package](https://github.com/ageitgey/face_recognition) 
* Flask
* OpenCV 
* FFMPEG
* Docker

## Installation
- To run this project, install it locally using pip on a virtual environment
```sh
pip install -r requirements.txt
```
- Install these software packages that application requires
  1. tesseract 
  2. ffmpeg 
  3. cmake
- Replace with your own path in the `TODO` of `ocr_process.py` and `orientation_processing.py`

You can test run the application by running the following command
```sh
python app.py
```
Then you can access the web app at `http://localhost:5000/`

## Building the Docker Container
Make sure you have Docker desktop installed on your machine. To deploy this project using Docker, follow these steps to build and run the docker container:

```sh
docker build -t face-matching .
docker run -p 8080:8080 face-matching
```
After running the above command, you can access the web app at `http://localhost:8080/`

## Deployment containers to the cloud
There is bunch of different options for deploying the docker container to the cloud.
You can use AWS Elastic Container Service, Google Cloud Run, or Azure Container Instances. 

But most of the time, you will need to tag and push your docker image to a container registry first.
You can run the following command to tag and push your docker image to any Cloud provider.
```sh
docker tag face-matching <your-cloud-provider>/<your-repo-name>:<tag>
docker push <your-cloud-provider>/<your-repo-name>:<tag>
```

## ~~Deployment with Heroku~~
Starting November 28, 2022, Heroku stop offering free product plans and plan to start shutting down free dynos and data services. Hence this option no longer feasible.
* ~~Deployment was done by using [Heroku](https://www.heroku.com/)~~ 
  * Procfile is used to specifies the commands that are executed by the app on startup.  
  * Aptfile is used to install additional software packages that application requires

## Issue with dlib when building for linux/amd64
if you try to build for linux/amd64 CPU architecture in docker container, you may encounter this [issue](https://github.com/davisking/dlib/issues/3038). For now, it is only able to build and run on linux/arm64. 

So, I would suggest to run and deploy the docker container on a machine with arm64 CPU architecture.

## Authors
[**Lim Kha Shing**](https://www.linkedin.com/in/lim-kha-shing-836a24120/)
