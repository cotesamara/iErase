from pathlib import Path

from PIL import Image, ImageSequence, UnidentifiedImageError

from image_processing_sawaab import remove_background, remove_background_ai

#---------------------------------------- ai shit -------------------------------------
def prepare_frame_for_gif(frame, alpha_threshold=128):
    # GIF cannot save smooth/partial transparency like PNG can.
    # It only know visible or invisible, so we make alpha into yes/no.
    rgba_frame = frame.convert("RGBA")
    alpha = rgba_frame.getchannel("A")

    # Quantize make the frame use a GIF colour palette.
    # Use only 255 colours so palette spot 255 stay free for transparency.
    palette_frame = rgba_frame.convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
    )

    # White in this mask means alpha is too low and pixel should disappear.
    transparent_mask = alpha.point(
        lambda value: 255 if value < alpha_threshold else 0
    )

    # Put all invisible pixels into palette spot 255.
    palette_frame.paste(255, mask=transparent_mask)
    palette_frame.info["transparency"] = 255
    palette_frame.info["disposal"] = 2
    return palette_frame

#---------------------------------------- ai shit -------------------------------------
def process_gif(
    input_path,
    output_path,
    threshold=85,
    method="pillow",
    model="u2netp",
    progress_callback=None,
):
    # input_path = where the old GIF is.
    # output_path = where we want the new GIF to save.
    # threshold = how hard the background remover should work.
    # method = use "pillow" or "ai" background removal.
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Stop early and give a clear error if the file is missing.
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Threshold must be a whole number from 0 to 255.
    if not isinstance(threshold, int) or not 0 <= threshold <= 255:
        raise ValueError("Threshold must be a whole number from 0 to 255.")

    if method not in {"pillow", "ai"}:
        raise ValueError('Method must be either "pillow" or "ai".')

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
                print(
                    f"Processing frame {frame_number + 1} of {total_frames} "
                    f"with {model if method == 'ai' else 'Pillow'}"
                )

                # Get this frame speed. Use 100 if no speed was saved.
                duration = frame.info.get("duration", 100)
                frame_durations.append(duration)

                # RGBA let our frame have invisible pixels.
                rgba_frame = frame.convert("RGBA")

                if method == "ai":
                    # AI mode use rembg and the chosen model.
                    cleaned_frame = remove_background_ai(rgba_frame, model=model)
                else:
                    # Pillow mode use our colour threshold method.
                    cleaned_frame = remove_background(rgba_frame, threshold)
                processed_frames.append(cleaned_frame)

                # Tell the app how many frames are done.
                # Terminal tests can leave progress_callback empty.
                if progress_callback is not None:
                    progress_callback(frame_number + 1, total_frames)

    # Pillow use this error when the file is not a real image.
    except UnidentifiedImageError as error:
        raise ValueError(f"Pillow cannot read this image: {input_path}") from error
    # Pillow can use OSError when an image file is broken.
    except OSError as error:
        raise ValueError(f"The GIF looks broken or cannot be read: {input_path}") from error

    # Make the output folder if it does not already exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Change RGBA frames into GIF-safe frames with real transparency.
    gif_frames = [prepare_frame_for_gif(frame) for frame in processed_frames]

    try:
        # Save first frame, then attach all other frames after it.
        gif_frames[0].save(
            output_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=frame_durations,
            loop=loop,
            disposal=2,
            transparency=255,
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
