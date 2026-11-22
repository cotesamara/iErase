

from PIL import Image , ImageSequence 
from image_processing_sawaab import remove_background

# Open our gif uisng the thingy u found 
gif = Image.open("assets/sample-sammy.gif")
# for the processing the done frames 
processed_frames = []
# for the processing the done frames durations
frame_durations = []

# frame_number tell us which frame we working on.
# frame is the actual picture from the GIF.
for frame_number, frame in enumerate(ImageSequence.Iterator(gif)):
    print("Working on frame:", frame_number)
    # Get frame speed, use 100 if gif got no speed saved
    duration = frame.info.get("duration", 100)
    frame_durations.append(duration)
    # change frame to rgbaso it can use transparencyyyyy
    rgba_frame = frame.convert("RGBA")
    # remove background from this frame
    cleaned_frame = remove_background(rgba_frame)
    # save cleaned frame inside our list
    processed_frames.append(cleaned_frame)


# save first frame then attach all other frames after it
processed_frames[0].save(
    "outputs/sawaab_transparent_sammy.gif",
    save_all=True,
    append_images=processed_frames[1:],
    duration=frame_durations,
    loop=gif.info.get("loop", 0),
    disposal=2,
)

print("gangangangngagan", len(processed_frames))
