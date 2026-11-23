from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QThread, Signal

from gif_processing import process_gif
from image_processing_sawaab import remove_background, remove_background_ai


class ProcessingWorker(QThread):
    """Run background removal without freezing the app window."""

    progress_changed = Signal(int)
    processing_finished = Signal(str)
    processing_failed = Signal(str)

    def __init__(
        self,
        input_path,
        output_path,
        method="pillow",
        threshold=85,
        model="u2net",
        parent=None,
    ):
        super().__init__(parent)
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.method = method
        self.threshold = threshold
        self.model = model

    def report_frame_progress(self, current_frame, total_frames):
        # Keep the last 5% for turning the frames back into a finished GIF.
        percent = round((current_frame / total_frames) * 95)
        self.progress_changed.emit(percent)

    def run(self):
        try:
            if self.input_path.suffix.lower() == ".gif":
                process_gif(
                    input_path=self.input_path,
                    output_path=self.output_path,
                    threshold=self.threshold,
                    method=self.method,
                    model=self.model,
                    progress_callback=self.report_frame_progress,
                )
            else:
                self.process_picture()

            self.processing_finished.emit(str(self.output_path))
        except (FileNotFoundError, UnidentifiedImageError, ValueError, OSError) as error:
            self.processing_failed.emit(str(error))
        except Exception as error:
            # Keep a model problem or other surprise from crashing the UX.
            self.processing_failed.emit(f"Background removal failed: {error}")

    def process_picture(self):
        if not self.input_path.is_file():
            raise FileNotFoundError(f"Input file does not exist: {self.input_path}")

        self.progress_changed.emit(10)

        with Image.open(self.input_path) as image:
            rgba_image = image.convert("RGBA")
            if self.method == "ai":
                result = remove_background_ai(rgba_image, model=self.model)
            else:
                result = remove_background(rgba_image, threshold=self.threshold)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(self.output_path, format="PNG")
        self.progress_changed.emit(95)
