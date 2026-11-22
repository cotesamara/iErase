from pathlib import Path

from PIL import Image, ImageSequence, UnidentifiedImageError

from image_processing_sawaab import remove_background


def process_gif(input_path, output_path, threshold=85):
    # input_path = where the old GIF is.
    # output_path = where we want the new GIF to save.
    # threshold = how hard the background remover should work.
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Stop early and give a clear error if the file is missing.
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Threshold must be a whole number from 0 to 255.
    if not isinstance(threshold, int) or not 0 <= threshold <= 255:
        raise ValueError("Threshold must be a whole number from 0 to 255.")

    try:
        # with will close the GIF for us when processing is done.
        with Image.open(input_path) as gif:
            # A normal image can open in Pillow too, so check it is really GIF.
            if gif.format != "GIF":
                raise ValueError(f"Input file is not a GIF: {input_path}")

            # total_frames = how many pictures are inside this GIF.
            total_frames = gif.n_frames

            # processed_frames hold every frame after background is gone.
            processed_frames = []

            # frame_durations hold how long every frame stay on screen.
            frame_durations = []

            # Save loop setting before the GIF file close.
            loop = gif.info.get("loop", 0)

            # frame_number start at 0 because Python count from 0.
            # frame is the actual picture we working on right now.
            for frame_number, frame in enumerate(ImageSequence.Iterator(gif)):
                # + 1 make progress nicer for humans, like 1 of 38.
                print(f"Processing frame {frame_number + 1} of {total_frames}")

                # Get this frame speed. Use 100 if no speed was saved.
                duration = frame.info.get("duration", 100)
                frame_durations.append(duration)

                # RGBA let our frame have invisible pixels.
                rgba_frame = frame.convert("RGBA")

                # Give the chosen threshold to our background remover.
                cleaned_frame = remove_background(rgba_frame, threshold)
                processed_frames.append(cleaned_frame)

    # Pillow use this error when the file is not a real image.
    except UnidentifiedImageError as error:
        raise ValueError(f"Pillow cannot read this image: {input_path}") from error
    # Pillow can use OSError when an image file is broken.
    except OSError as error:
        raise ValueError(f"The GIF looks broken or cannot be read: {input_path}") from error

    # Make the output folder if it does not already exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Save first frame, then attach all other frames after it.
        processed_frames[0].save(
            output_path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=frame_durations,
            loop=loop,
            disposal=2,
        )
    except OSError as error:
        raise OSError(f"Could not save the finished GIF: {output_path}") from error

    print(f"Finished! Saved {total_frames} frames to: {output_path}")

    # Return path so another file or our future UI can use it.
    return output_path


# This part only run when we start gif_processing.py by itself.
if __name__ == "__main__":
    try:
        process_gif(
            input_path="assets/sample-sammy.gif",
            output_path="outputs/sawaab_transparent_sammy.gif",
            threshold=85,
        )
    except (FileNotFoundError, ValueError, OSError) as error:
        print("ERROR:", error)
        raise SystemExit(1)
