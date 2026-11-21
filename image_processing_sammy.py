from PIL import Image, ImageDraw

def remove_background(frame):
    frame = frame.convert("RGBA")
    start = (0, 0)
    replace = (0, 0, 0, 0)
    ImageDraw.floodfill(frame, start, replace, thresh=50)
    return frame