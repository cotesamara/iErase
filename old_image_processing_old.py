
from PIL import Image
#
def remove_background(image):
     # Convert the image to RGBA so it supports transparency
    # R=red and G=geen and guess waht B is blue a new thingy here is  A = Alpha which is transparency
    image = image.convert("RGBA") 


    # Read the colour of the pixel in the top left corner for the flood fill algorithm
    start_pixel = image.getpixel((0, 0))
    print("Starting pixel:", start_pixel)


    #loop through every row of pixels yis our vertical position and x is our horizontal position
    for y in range(image.height):
        for x in range(image.width):

            # Get the RGBA values of the pixel at pos x and y
            # each value can be from 0 to 255
            r, g, b, a = image.getpixel((x, y))


            # Check if the pixel is nearly white
            # All three RGB values must be greater than 240 for it to be white i google this shit lmao 
            if r > 240 and g > 240 and b > 240:

                # Make the pixel transparent alpha = 0
                # Keep its original RGB values unchanged cause we dont want to mess upt he first image
                # alpha 0 = invisible and alpha 255 = fully visible
                image.putpixel((x, y), (r, g, b, 0))

    return image
