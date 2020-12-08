# https://github.com/0x64746b/python-cpbd
# https://stackoverflow.com/questions/7765810/is-there-a-way-to-detect-if-an-image-is-blurry/
# https://stackoverflow.com/questions/6646371/detect-which-image-is-sharper
# https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

from skimage.io import imread

from src.cpbd import compute


# Calculate both image sharpness metric and find the differences
def calculate_sharpness(known_image_path, cropped_image_path):
    known_image = imread(known_image_path, pilmode='L')
    cropped_image = imread(cropped_image_path, pilmode='L')
    return compute(known_image) - compute(cropped_image)

# Many people suggest this method. But not gonna use this
# def variance_of_laplacian(image_path):
#     # compute the Laplacian of the image and then return the focus
#     # measure, which is simply the variance of the Laplacian
#     image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
#     return cv2.Laplacian(image, cv2.CV_64F).var()


# Another way to determine is to measure the quantity of the gradient.
# im = Image.open(blur).convert('L') # to grayscale
# array = np.asarray(im, dtype=np.int32)
# gy, gx = np.gradient(array)
# gnorm = np.sqrt(gx**2 + gy**2)
# sharpness = np.average(gnorm)
# print(sharpness)
