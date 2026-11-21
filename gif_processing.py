

from PIL import Image
from image_processing import remove_background

# Open our gif uisng the thingy u found 
gif = Image.open("assets/sample.gif")

# check how many frames our gif as 
print("Number of frames:", gif.n_frames)

# select the first frame
gif.seek(0)

# convert it to RGBA
frame = gif.convert("RGBA")

# Use our background removal function
result = remove_background(frame)

# save the processed frame as a PNG
result.save("outputs/first_frame.png")

print("1st frame processed gang gang!")
