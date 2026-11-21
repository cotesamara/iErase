from PIL import Image, ImageDraw
from rembg import remove, new_session

#starts session with ai model once so we dont have to do it multiple times
session = new_session()

def remove_solid_background(frame):
    # Convert the image to RGBA so it supports transparency
    frame = frame.convert("RGBA")
    # choose which pixel will be the starting point
    start = (0, 0)
    # replacement color in this case transparent so it changes the color of the specifi pixel we're at
    replace = (0, 0, 0, 0)
    # starts at aa given pixel location
    # starts moving to neighbouring pixels and checking if they are similar to starting pixel
    # replaces pixel with given color and stops when the difference is too great
    ImageDraw.floodfill(frame, start, replace, thresh=15)
    return frame

def ai_remove_background(frame):
    # Convert the image to RGBA so it supports transparency
    rgba = frame.convert("RGBA")
    #remove background
    result = remove(rgba, session=session)
    return result
