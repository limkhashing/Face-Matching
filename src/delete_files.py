import shutil


def delete_files(request_upload_folder_path, request_frames_folder_path):
    shutil.rmtree(request_upload_folder_path, ignore_errors=True)
    shutil.rmtree(request_frames_folder_path, ignore_errors=True)
