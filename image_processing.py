
from PIL import Image

def remove_background(image):
    image = image.convert("RGBA")

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = image.getpixel((x, y))

            if r > 240 and g > 240 and b > 240:
                image.putpixel((x, y), (r, g, b, 0))

    return image
