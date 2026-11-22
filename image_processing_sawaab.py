from PIL import Image, ImageDraw, ImageFilter


def remove_background(image):

    # Make the image use RGBA colours
    # R is red G = green, B = blue and A which is alpha istransparency
    # a= 255 means its sup-er visible and a= 0 means its invisible.
    image = image.convert("RGBA")

    # background_colour = colour from top left pixel at (0, 0).
    # We are guessing top left is part of the white background
    #we need to make this a var later or update it to be more dynamic for different gifs
    background_colour = image.getpixel((0, 0))
    print("Starting pixel", background_colour)

    # threshold = how different a colour is allowed to be
    # Small number only remove colours super close to the background
    # Big number remove more colours but it can eat the character too
    threshold = 85

    # width her eis how many pixels go left to right
    # height here is how many pixels go top to bottom its the easiest way to find size of the image
    width, height = image.size

    # border_pixels = list holding pixel spots around the outside edge
    # Checking all edges help remove every white background part
    border_pixels = (
        # x left and right
        # y up and down

        # all top pixels y stay 0 & x keep changing
        [(x, 0) for x in range(width)]
        #all bottom pixels y stay at the last row
        + [(x, height - 1) for x in range(width)]
        #all left pixels x stay 0 & y keep changing
        + [(0, y) for y in range(height)]
        #all right pixels x stay at the last colum
        + [(width - 1, y) for y in range(height)] )

    # This loop check every spot around the image edge
    for position in border_pixels:
        pixel = image.getpixel(position)

        # colourdif = biggest colour difference we found
        # channel = which colour number we checking right now
        # channel 0 is red, 1 is green and 2 is blue
        colour_difference = max(
            abs(pixel[channel] - background_colour[channel])
            for channel in range(3)
        )

        # pixel[3] means the alpha number from this pixel
        # != 0 mean pixel is not already invisible idk copilot suggested this idfk 
        # <= threshold mean its colour is close enough to background thiswhat my idea for the eyes
        if pixel[3] != 0 and colour_difference <= threshold:
            # Flood fill start at this position
            # It move into touching pixels with close colours
            # value is the new colour we give those background pixels
            # 0000 mean black but fully invisible
            ImageDraw.floodfill(
                image,
                xy=position,
                value=(0, 0, 0, 0),
                thresh=threshold,
            )


    # MinFilter(3) push invisible area in about one pixel
    # This help get rid of skinny white line around character
    alpha = image.getchannel("A").filter(ImageFilter.MinFilter(3))

    # Put the cleaned alpha back into the image.
    image.putalpha(alpha)

    return image
