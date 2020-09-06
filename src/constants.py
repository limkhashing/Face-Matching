# ''''''
# Constant variables that need to be refer
# ''''''

# Extensions for images and videos
ALLOWED__PICTURE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')
ALLOWED_VIDEO_EXTENSIONS = ('mp4', 'avi', 'webm', 'mov')

# Constant variable for directory
frames_folder = "./frames"
upload_folder = "./upload"

# Constant threshold for resizing
frame_size_threshold = 200000
image_size_threshold = 500000
max_resize = 40000

# key strings source type checking
source_type_image = "image"
source_type_video = "video"
