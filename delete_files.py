import os
from constants import frames_folder, upload_folder


def delete_files():
    for file in os.listdir(frames_folder):
        file_path = os.path.join(frames_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    for file in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)