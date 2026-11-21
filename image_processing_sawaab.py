
from PIL import Image, ImageDraw
#
def remove_background(image):
     # Convert the image to RGBA so it supports transparency
    # R=red and G=geen and guess waht B is blue a new thingy here is  A = Alpha which is transparency
    image = image.convert("RGBA") 


    # Read the colour of the pixel in the top left corner for the flood fill algorithm
    start_pixel = image.getpixel((0, 0))
    print("Starting pixel:", start_pixel)


    # ff  starts at (0, 0)
    # it checks connected pixels with similar colours
    # instead of removing every white pixel in the image
    ImageDraw.floodfill(
        image,
        xy=(0, 0),              # starting position
        value=(255, 255, 255, 0), # make the background transparent
        thresh=20               # allow some colour differences
    )
    return image