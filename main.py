#from image_processing_sammy import remove_solid_background, ai_remove_background

#gif = Image.open("assets/sample.gif")
#gif.seek(2)

#no_ai_result = remove_solid_background(gif)
#ai_result = ai_remove_background(gif)

#no_ai_result.save("outputs/sample_output-_aiSammy.png")
#ai_result.save("outputs/sample_output_noaiSammy.png")

#print("Background removed successfully!")
import math
import os
import random
import shutil
import tempfile
from pathlib import Path
from PIL import Image
import sys
from uuid import uuid4
from PySide6.QtCore import QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QImageReader,
    QMovie,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, 
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel, 
    QMainWindow, 
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout, 
    QWidget,
    )


def bundled_path(relative_path=""):
    """Find a project file both in source code and inside the packaged app."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


# The packaged app carries its own u2net model so AI works without internet.
if getattr(sys, "frozen", False):
    os.environ["REMBG_HOME"] = str(bundled_path())


from processing_worker import ProcessingWorker


class CheckerboardCanvas(QWidget):
    """Displays an image or animated GIF on top of a pastel transparency checkerboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(290, 235)
        self._movie = None
        self._pixmap = None

        # Inner label that holds either the animated GIF movie or static picture
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        self.media_label = QLabel()
        self.media_label.setAlignment(Qt.AlignCenter)
        self.media_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.media_label)

    def show_file(self, path: str):
        # Stop any old GIF animation first
        self.clear_preview()

        if path.lower().endswith(".gif"):
            movie = QMovie(path)

            # Read the full GIF canvas without loading/caching frame 0 first.
            # Every frame must use one fixed size or the preview can look like
            # it zooms when the animation loops back to the first frame.
            orig_size = QImageReader(path).size()
            if not orig_size.isEmpty():
                scaled = orig_size.scaled(QSize(265, 210), Qt.KeepAspectRatio)
                movie.setScaledSize(scaled)

            movie.setCacheMode(QMovie.CacheAll)
            self._movie = movie
            self.media_label.setMovie(movie)
            movie.start()
        else:
            pix = QPixmap(path)
            if not pix.isNull():
                self._pixmap = pix.scaled(
                    265, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.media_label.setPixmap(self._pixmap)
            else:
                self.media_label.setText("Could not load preview")

    def clear_preview(self):
        # Clean up any active movie or picture when the preview closes
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        self._pixmap = None
        self.media_label.clear()

    def paintEvent(self, event):
        # Draw a soft pastel pink & white checkerboard to show clear backgrounds
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        clip = QPainterPath()
        clip.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        painter.setClipPath(clip)

        tile = 14
        light = QColor("#FFFFFF")
        tint = QColor("#F8E8EB")

        for y in range(0, self.height(), tile):
            for x in range(0, self.width(), tile):
                is_even = ((x // tile) + (y // tile)) % 2 == 0
                painter.fillRect(x, y, tile, tile, light if is_even else tint)

        painter.setClipping(False)
        painter.setPen(QPen(QColor("#E3B8C1"), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0.5, 0.5, self.width() - 1, self.height() - 1, 14, 14)


class PreviewCard(QFrame):
    """Left-side split-screen preview box with a top-right 'X' button to close it."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewCard")
        self.setFixedWidth(322)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        # Header row: "Preview" label on the left, circular "X" close button on the right
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.header_title = QLabel("Preview")
        self.header_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #8A5A66; background: transparent; border: none;"
        )

        self.close_btn = QPushButton("✕")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setToolTip("Close preview")
        self.close_btn.clicked.connect(self.close_panel)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(195, 144, 155, 0.25);
                color: #8A5A66;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 13px;
            }
            QPushButton:hover {
                background-color: #C3909B;
                color: #FFFFFF;
            }
        """)

        header_row.addWidget(self.header_title)
        header_row.addStretch()
        header_row.addWidget(self.close_btn)
        layout.addLayout(header_row)

        # Checkerboard image/GIF preview area
        self.canvas = CheckerboardCanvas()
        layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            #PreviewCard {
                background-color: rgba(255, 255, 255, 0.65);
                border: 2px dashed #C3909B;
                border-radius: 18px;
            }
        """)

    def open_with_file(self, path: str):
        # Load the finished image/GIF into the preview and show the split-screen panel
        self.canvas.show_file(path)
        self.show()

    def close_panel(self):
        # Hide the preview panel and return to the centered single-column layout
        self.canvas.clear_preview()
        self.hide()
        self.closed.emit()


class FlowerSlider(QWidget):
    """Vertical slider with a pink cherry blossom flower you can drag up and down."""

    value_changed = Signal(int)

    def __init__(self, minimum=1, maximum=255, value=22, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self._value = value
        self._dragging = False
        self.setFixedSize(44, 155)
        self.setCursor(Qt.PointingHandCursor)

    @property
    def value(self) -> int:
        return self._value

    def set_number(self, new_val: int):
        # Keep the number between the lowest and highest allowed values
        safe_val = max(self.minimum, min(self.maximum, int(new_val)))
        if safe_val != self._value:
            self._value = safe_val
            self.value_changed.emit(self._value)
            self.update()  # Redraw the flower at its new spot

    def y_to_number(self, y: float) -> int:
        # Turn the mouse's up-and-down position into a slider number
        pad = 16.0
        track_height = self.height() - 2 * pad
        percent = 1.0 - max(0.0, min(1.0, (y - pad) / track_height))
        return round(self.minimum + percent * (self.maximum - self.minimum))

    def number_to_y(self) -> float:
        # Turn the current slider number into an up-and-down spot on the bar
        pad = 16.0
        track_height = self.height() - 2 * pad
        percent = (self._value - self.minimum) / (self.maximum - self.minimum)
        return pad + (1.0 - percent) * track_height

    def mousePressEvent(self, event):
        # Move the flower right where the user clicks
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self.set_number(self.y_to_number(event.position().y()))

    def mouseMoveEvent(self, event):
        # Move the flower while the user drags the mouse
        if self._dragging:
            self.set_number(self.y_to_number(event.position().y()))

    def mouseReleaseEvent(self, event):
        # Stop dragging when the user lets go of the mouse button
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def wheelEvent(self, event):
        # Let the user scroll the mouse wheel to nudge the number up or down
        step = 2 if event.angleDelta().y() > 0 else -2
        self.set_number(self._value + step)

    def paintEvent(self, event):
        # Draw the vertical bar and the 5-petal pink flower handle
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2.0
        pad = 16.0
        top_y = pad
        bottom_y = self.height() - pad
        flower_y = self.number_to_y()

        # Draw the light background bar
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 175))
        painter.drawRoundedRect(center_x - 3.5, top_y, 7, bottom_y - top_y, 3.5, 3.5)

        # Draw the pink filled part below the flower
        painter.setBrush(QColor("#D89BA8"))
        painter.drawRoundedRect(center_x - 3.5, flower_y, 7, bottom_y - flower_y, 3.5, 3.5)

        # Draw a thin border around the bar
        painter.setPen(QPen(QColor("#E3B8C1"), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(center_x - 3.5, top_y, 7, bottom_y - top_y, 3.5, 3.5)

        # Move to the flower's spot and draw the 5 petals
        painter.save()
        painter.translate(center_x, flower_y)

        # Soft shadow under the flower
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(168, 100, 117, 55))
        painter.drawEllipse(QPointF(0, 1.5), 13.5, 13.5)

        # Draw 5 pink petals in a circle
        for i in range(5):
            painter.save()
            painter.rotate(i * 72)
            petal = QPainterPath()
            petal.moveTo(0, 0)
            petal.cubicTo(-6.5, -4.5, -7.5, -12.5, -1.8, -14.2)
            petal.lineTo(0, -11.5)  # Little notch at the tip of each petal
            petal.lineTo(1.8, -14.2)
            petal.cubicTo(7.5, -12.5, 6.5, -4.5, 0, 0)
            painter.setBrush(QColor("#FFB7C5"))
            painter.setPen(QPen(QColor("#D98296"), 0.9))
            painter.drawPath(petal)
            painter.restore()

        # Draw the center dot of the flower
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#A86475"))
        painter.drawEllipse(QPointF(0, 0), 3.0, 3.0)
        painter.setBrush(QColor("#FFF3F6"))
        painter.drawEllipse(QPointF(0, 0), 1.3, 1.3)

        painter.restore()


class ThresholdBar(QWidget):
    """Side panel with the 'Thresh' title, number badge, and flower slider."""

    threshold_changed = Signal(int)

    def __init__(self, initial_value=22, parent=None):
        super().__init__(parent)
        self.setFixedWidth(68)

        layout = QVBoxLayout(self)
        # Push it down slightly so it lines up next to the upload box
        layout.setContentsMargins(0, 52, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.title_label = QLabel("Thresh")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #8A5A66; background: transparent;"
        )

        self.value_badge = QLabel(str(initial_value))
        self.value_badge.setAlignment(Qt.AlignCenter)
        self.value_badge.setFixedWidth(36)
        self.value_badge.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: #C3909B;
            border-radius: 8px;
            padding: 1px 6px;
        """)

        self.slider = FlowerSlider(minimum=1, maximum=255, value=initial_value)
        self.slider.value_changed.connect(self.update_number)

        layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.value_badge, alignment=Qt.AlignCenter)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)

    @property
    def value(self) -> int:
        return self.slider.value

    def update_number(self, new_val: int):
        # Update the number badge whenever the flower moves
        self.value_badge.setText(str(new_val))
        self.threshold_changed.emit(new_val)


class ModePicker(QFrame):
    """Toggle bar at the top that lets you switch between Pillow and AI."""

    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModePill")
        self.setFixedSize(500, 46)
        self.current_mode = "solid"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)

        self.pillow_btn = QPushButton("Pillow (Easy and Fast)")
        self.ai_btn = QPushButton("AI (Complex Bgs)")

        for btn in (self.pillow_btn, self.ai_btn):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)

        self.pillow_btn.setChecked(True)

        # Make sure only one mode button can be selected at a time
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.pillow_btn)
        self.group.addButton(self.ai_btn)

        self.pillow_btn.clicked.connect(lambda: self.pick_mode("solid"))
        self.ai_btn.clicked.connect(lambda: self.pick_mode("ai"))

        layout.addWidget(self.pillow_btn)
        layout.addWidget(self.ai_btn)

        self.setStyleSheet("""
            #ModePill {
                background-color: rgba(255, 255, 255, 0.58);
                border: 1.5px solid #E3B8C1;
                border-radius: 23px;
            }
            QPushButton {
                background-color: transparent;
                color: #8A5A66;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 17px;
                padding: 4px 14px;
            }
            QPushButton:hover:!checked {
                background-color: rgba(210, 210, 218, 0.35);
            }
            QPushButton:checked {
                background-color: #C3909B;
                color: #FFFFFF;
            }
        """)

    def pick_mode(self, mode: str):
        # Save whichever mode the user clicked
        self.current_mode = mode
        self.mode_changed.emit(mode)


class LoadingBar(QWidget):
    """Progress bar that shows how far along the background removal is."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoadingCard")
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 2)
        layout.setSpacing(6)

        # Top row with status text on the left and percentage on the right
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("Removing background.")
        self.status_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #8A5A66; background: transparent; border: none;"
        )

        self.percent_badge = QLabel("0%")
        self.percent_badge.setAlignment(Qt.AlignCenter)
        self.percent_badge.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: #C3909B;
            border-radius: 9px;
            padding: 2px 9px;
        """)

        header_row.addWidget(self.status_label)
        header_row.addStretch()
        header_row.addWidget(self.percent_badge)
        layout.addLayout(header_row)

        # Pink gradient progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.65);
                border: 1.5px solid #E3B8C1;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #FFC8D6,
                    stop: 0.5 #E598A8,
                    stop: 1 #A86475
                );
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            #LoadingCard {
                background: transparent;
                border: none;
            }
        """)

        # Timer that cycles the dots (".", "..", "...") while loading
        self._dot_step = 1
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self.move_dots)

    def start_loading(self):
        # Reset the bar to 0% and show it on screen
        self.set_percent(0)
        self._dot_step = 1
        self.status_label.setText("Removing background.")
        self._dot_timer.start(380)
        self.show()

    def set_percent(self, percent: int):
        # Update the bar and percentage badge
        safe_percent = max(0, min(100, int(percent)))
        self.progress_bar.setValue(safe_percent)
        self.percent_badge.setText(f"{safe_percent}%")
        if safe_percent >= 100:
            self._dot_timer.stop()
            self.status_label.setText("Background removed!")

    def move_dots(self):
        # Cycle between 1, 2, and 3 dots at the end of the text
        self._dot_step = (self._dot_step % 3) + 1
        self.status_label.setText("Removing background" + "." * self._dot_step)


class UploadBox(QFrame):
    """Dashed box where you can click to pick a file or drag and drop one."""

    file_selected = Signal(str)

    ALLOWED_EXTS = (".gif", ".png", ".jpg", ".jpeg")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(500, 195)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self.main_text = QLabel("Upload your GIF/Picture here")
        self.main_text.setAlignment(Qt.AlignCenter)
        self.main_text.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #8A5A66; background: transparent; border: none;"
        )

        self.sub_text = QLabel(".gif, .png, .jpg, .jpeg")
        self.sub_text.setAlignment(Qt.AlignCenter)
        self.sub_text.setStyleSheet(
            "font-size: 12px; color: #A67B86; background: transparent; border: none;"
        )

        layout.addWidget(self.main_text)
        layout.addWidget(self.sub_text)

        self.set_box_look(dragging=False)

    def set_box_look(self, dragging: bool):
        # Change the box color when dragging a file over it or hovering
        if dragging:
            self.setStyleSheet("""
                #DropZone {
                    background-color: rgba(210, 210, 218, 0.55);
                    border: 2.5px dashed #A86475;
                    border-radius: 18px;
                }
            """)
        else:
            self.setStyleSheet("""
                #DropZone {
                    background-color: rgba(255, 255, 255, 0.55);
                    border: 2px dashed #C3909B;
                    border-radius: 18px;
                }
                #DropZone:hover {
                    background-color: rgba(210, 210, 218, 0.55);
                    border: 2px dashed #A86475;
                }
            """)

    def mousePressEvent(self, event):
        # Open the Mac file finder when the user clicks inside the box
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Choose a GIF or Picture",
                "",
                "Images & GIFs (*.gif *.png *.jpg *.jpeg)",
            )
            if path:
                self.save_picked_file(path)

    def dragEnterEvent(self, event):
        # Highlight the box if the dragged file is a supported image or GIF
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(self.ALLOWED_EXTS):
                    event.acceptProposedAction()
                    self.set_box_look(dragging=True)
                    self.main_text.setText("Drop it right here!")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        # Reset the box look if the user drags the file away without dropping it
        self.set_box_look(dragging=False)
        if not getattr(self, "current_file", None):
            self.main_text.setText("Upload your GIF/Picture here")

    def dropEvent(self, event):
        # Grab the file path when the user drops a file into the box
        self.set_box_look(dragging=False)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(self.ALLOWED_EXTS):
                self.save_picked_file(path)
                event.acceptProposedAction()
                return

    def save_picked_file(self, path: str):
        # Show the file name in the box and tell the main window a file was picked
        self.current_file = path
        filename = path.rsplit("/", 1)[-1]
        self.main_text.setText(filename)
        self.sub_text.setText("Upload or drag another file to replace")
        self.file_selected.emit(path)


class FallingPetals(QWidget):
    """Clear layer over the whole window that draws falling pink petals."""

    def __init__(self, parent=None, count=22):
        super().__init__(parent)
        # Let mouse clicks pass right through the petals to the buttons below
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.petal_colors = [
            QColor("#FFB7C5"),  # cherry blossom pink
            QColor("#FFC8D6"),  # pastel pink
            QColor("#FF9EB5"),  # deeper pink 
            QColor("#FFE4EC"),  #  pale pink
        ]

        self.petals = [self.make_petal(random_y=True) for _ in range(count)]
        self.burst_petals = []  # Extra celebration petals thrown at 100%

        # Update the petal positions roughly 60 times a second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_petals)
        self.timer.start(16)  # ~60 FPS

    def make_petal(self, random_y=False):
        # Create one petal with random size, speed, sway, and pink shade
        w = max(self.width(), 980)
        h = max(self.height(), 620)
        return {
            "x": random.uniform(0, w),
            "y": random.uniform(0, h) if random_y else random.uniform(-60, -10),
            "size": random.uniform(7, 13),
            "speed_y": random.uniform(0.7, 1.6),
            "sway_amp": random.uniform(0.4, 1.2),
            "sway_freq": random.uniform(0.015, 0.035),
            "phase": random.uniform(0, math.tau),
            "angle": random.uniform(0, 360),
            "spin": random.uniform(-1.5, 1.5),
            "color": random.choice(self.petal_colors),
        }

    def celebrate_burst(self, origin: QPointF | None = None, amount: int = 55):
        # Throw a joyful fountain of cherry blossom petals when progress hits 100%
        cx = origin.x() if origin is not None else self.width() / 2.0
        cy = origin.y() if origin is not None else self.height() * 0.45

        for _ in range(amount):
            # Shoot mostly upward and outward like confetti
            launch_angle = random.uniform(-math.pi * 0.88, -math.pi * 0.12)
            speed = random.uniform(4.5, 11.5)
            self.burst_petals.append({
                "x": cx + random.uniform(-90, 90),
                "y": cy + random.uniform(-20, 20),
                "vx": math.cos(launch_angle) * speed,
                "vy": math.sin(launch_angle) * speed,
                "gravity": random.uniform(0.14, 0.24),
                "drag": 0.985,
                "size": random.uniform(8, 15),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-6.0, 6.0),
                "sway_phase": random.uniform(0, math.tau),
                "color": random.choice(self.petal_colors),
            })

    def move_petals(self):
        # Gently drift and spin each petal downward
        w = self.width()
        h = self.height()
        for p in self.petals:
            p["phase"] += p["sway_freq"]
            p["x"] += math.sin(p["phase"]) * p["sway_amp"]
            p["y"] += p["speed_y"]
            p["angle"] = (p["angle"] + p["spin"]) % 360

            # Put the petal back at the top once it falls off the bottom
            if p["y"] > h + 20 or p["x"] < -30 or p["x"] > w + 30:
                p.update(self.make_petal(random_y=False))

        # Move any celebration burst petals and remove them once they fall off screen
        still_flying = []
        for bp in self.burst_petals:
            bp["vx"] *= bp["drag"]
            bp["vy"] = bp["vy"] * bp["drag"] + bp["gravity"]
            bp["sway_phase"] += 0.08
            bp["x"] += bp["vx"] + math.sin(bp["sway_phase"]) * 0.6
            bp["y"] += bp["vy"]
            bp["angle"] = (bp["angle"] + bp["spin"]) % 360

            if bp["y"] <= h + 30 and -40 <= bp["x"] <= w + 40:
                still_flying.append(bp)
        self.burst_petals = still_flying

        self.update()  # Redraw all petals

    def _draw_single_petal(self, painter: QPainter, p: dict):
        painter.save()
        painter.translate(p["x"], p["y"])
        painter.rotate(p["angle"])
        painter.setBrush(p["color"])

        # Draw a curved petal shape
        s = p["size"]
        path = QPainterPath()
        path.moveTo(0, -s * 0.6)
        path.cubicTo(s * 0.65, -s * 0.25, s * 0.55, s * 0.55, 0, s * 0.7)
        path.cubicTo(-s * 0.55, s * 0.55, -s * 0.65, -s * 0.25, 0, -s * 0.6)
        painter.drawPath(path)

        painter.restore()

    def paintEvent(self, event):
        # Draw each petal on the screen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        for p in self.petals:
            self._draw_single_petal(painter, p)

        for bp in self.burst_petals:
            self._draw_single_petal(painter, bp)


class IEraseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("iErase")
        self.resize(980, 620)
        self.selected_file_path = None
        self.processed_file_path = None
        self.processing_worker = None

        #create widget and name it
        central_widget = QWidget()
        central_widget.setObjectName("MainBackground")
        self.setCentralWidget(central_widget)

        # Split the window into Top, Middle, and Bottom sections
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        #TOP ROW
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        # Put the eraser logo and "iErase" title side by side in the top-left
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(24, 24, 0, 0)
        brand_row.setSpacing(10)

        logo_pic = self.load_picture("assets/EraserLogo.png", height=35)
        title = QLabel("iErase")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #C3909B;")

        brand_row.addWidget(logo_pic, alignment=Qt.AlignVCenter)
        brand_row.addWidget(title, alignment=Qt.AlignVCenter)

        top_right_pic = self.load_picture("assets/cherryBlossomTop.png", height=110)

        top_row.addLayout(brand_row)
        top_row.setAlignment(brand_row, Qt.AlignTop | Qt.AlignLeft)
        top_row.addStretch()  # Pushes top_right_pic all the way to the right
        top_row.addWidget(top_right_pic, alignment=Qt.AlignTop | Qt.AlignRight)
        main_layout.addLayout(top_row)


        #MIDDLE ROW
        main_layout.addStretch(1)

        # Horizontal row holding the split-screen preview card on the left and controls on the right
        center_row = QHBoxLayout()
        center_row.setContentsMargins(24, 0, 24, 0)
        center_row.setSpacing(18)
        center_row.addStretch()

        # Empty spacer on the left to balance the threshold slider when preview is closed
        self.left_spacer = QWidget()
        self.left_spacer.setFixedWidth(68)
        center_row.addWidget(self.left_spacer)

        # Split-screen preview panel on the left (opens at 100% and closes with X or new file)
        self.preview_card = PreviewCard()
        self.preview_card.hide()
        self.preview_card.closed.connect(self.on_preview_closed)
        center_row.addWidget(self.preview_card, alignment=Qt.AlignTop)

        # Vertical stack for the mode toggle, upload box, loading bar, and action buttons
        center_stack = QVBoxLayout()
        center_stack.setContentsMargins(0, 0, 0, 0)
        center_stack.setSpacing(0)

        self.mode_selector = ModePicker()
        center_stack.addWidget(self.mode_selector, alignment=Qt.AlignCenter)

        center_stack.addSpacing(6)
        self.drop_zone = UploadBox()
        self.drop_zone.file_selected.connect(self.file_picked)
        center_stack.addWidget(self.drop_zone, alignment=Qt.AlignCenter)

        self.loading_card = LoadingBar()
        self.loading_card.hide()  # Hidden until the user clicks "Remove Background"
        center_stack.addWidget(self.loading_card, alignment=Qt.AlignCenter)

        center_stack.addSpacing(28)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)

        # Main button to start removing the background
        self.remove_btn = QPushButton("Remove Background")
        self.remove_btn.setEnabled(False)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setFixedSize(295, 44)
        self.remove_btn.clicked.connect(self.start_erasing)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #D89BA8,
                    stop: 1 #B57382
                );
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover:enabled {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #C98896,
                    stop: 1 #A16070
                );
            }
            QPushButton:disabled {
                background-color: rgba(195, 144, 155, 0.35);
                color: rgba(255, 255, 255, 0.75);
            }
        """)

        # Button to save the finished file (unlocks when progress hits 100%)
        self.download_btn = QPushButton("Download")
        self.download_btn.setEnabled(False)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setFixedSize(193, 44)
        self.download_btn.clicked.connect(self.save_file)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.8);
                color: #8A5A66;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #C3909B;
                border-radius: 22px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(210, 210, 218, 0.55);
                border-color: #A86475;
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.35);
                color: rgba(138, 90, 102, 0.45);
                border: 2px solid rgba(195, 144, 155, 0.35);
            }
        """)

        actions_row.addWidget(self.remove_btn)
        actions_row.addWidget(self.download_btn)

        actions_container = QWidget()
        actions_container.setFixedWidth(500)
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addLayout(actions_row)
        center_stack.addWidget(actions_container, alignment=Qt.AlignCenter)

        # Extra stretch at the bottom keeps the threshold bar from shifting when loading appears
        center_stack.addStretch()

        center_row.addLayout(center_stack)

        # Flower threshold slider on the right side of the upload box
        self.threshold_control = ThresholdBar(initial_value=22)
        self.threshold_control.threshold_changed.connect(self.threshold_moved)
        center_row.addWidget(self.threshold_control, alignment=Qt.AlignTop)

        center_row.addStretch()

        main_layout.addLayout(center_row)

        main_layout.addStretch(2)

        #BOTTOM ROW
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_left_pic = self.load_picture("assets/cherryBlossomBottom.png", height=200)
        bottom_row.addWidget(bottom_left_pic, alignment=Qt.AlignBottom | Qt.AlignLeft)
        bottom_row.addStretch()  # Keeps bottom_left_pic pinned to the left
        main_layout.addLayout(bottom_row)

        # Falling petal animation layer covering the whole window
        self.petal_overlay = FallingPetals(central_widget, count=22)
        self.petal_overlay.resize(self.size())

        #do pastel background
        self.setStyleSheet("""
            #MainBackground {
                background-color: #F5E2E3;
            }
        """)

    def open_preview_split(self, preview_path: str):
        # Hide the left balancing spacer so the split view centers cleanly across the window
        self.left_spacer.hide()
        self.preview_card.open_with_file(preview_path)

    def on_preview_closed(self):
        # Restore the left spacer so the upload box re-centers when the preview is closed
        self.left_spacer.show()

    def threshold_moved(self, value: int):
        # Runs whenever the user drags the flower threshold slider
        print("Threshold:", value)

    def file_picked(self, path: str):
        # Runs when a user uploads or drops a file into the dashed box
        self.selected_file_path = path
        self.processed_file_path = None
        self.remove_btn.setEnabled(True)
        self.download_btn.setEnabled(False)
        self.loading_card.hide()

        # Automatically close the preview panel if a new file is chosen
        if self.preview_card.isVisible():
            self.preview_card.close_panel()

        print("Selected file:", path)

    def start_erasing(self):
        # Runs when the user clicks "Remove Background"
        if not self.selected_file_path:
            return
        method = "ai" if self.mode_selector.current_mode == "ai" else "pillow"
        input_path = Path(self.selected_file_path)
        output_suffix = ".gif" if input_path.suffix.lower() == ".gif" else ".png"
        output_path = Path(tempfile.gettempdir()) / f"ierase_{uuid4().hex}{output_suffix}"

        print(
            f"Running mode: {method} "
            f"(thresh={self.threshold_control.value}) on {self.selected_file_path}"
        )
        self.remove_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.set_input_controls_enabled(False)
        self.loading_card.start_loading()

        # The worker keeps slow AI processing away from the window thread.
        self.processing_worker = ProcessingWorker(
            input_path=input_path,
            output_path=output_path,
            method=method,
            threshold=self.threshold_control.value,
            model="u2net",
            parent=self,
        )
        self.processing_worker.progress_changed.connect(self.loading_card.set_percent)
        self.processing_worker.processing_finished.connect(self.processing_complete)
        self.processing_worker.processing_failed.connect(self.processing_error)
        self.processing_worker.start()

    def processing_complete(self, output_path: str):
        self.processed_file_path = output_path
        self.loading_card.set_percent(100)
        self.remove_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.set_input_controls_enabled(True)

        # Show Samara's preview with the real processed file.
        self.open_preview_split(output_path)

        box_center = self.drop_zone.mapTo(
            self.centralWidget(), self.drop_zone.rect().center()
        )
        self.petal_overlay.celebrate_burst(origin=QPointF(box_center))

    def processing_error(self, message: str):
        self.processed_file_path = None
        self.loading_card._dot_timer.stop()
        self.loading_card.status_label.setText("Could not remove background")
        self.remove_btn.setEnabled(True)
        self.download_btn.setEnabled(False)
        self.set_input_controls_enabled(True)
        QMessageBox.critical(self, "Background Removal Error", message)

    def set_input_controls_enabled(self, enabled: bool):
        # Do not let the selected file or mode change halfway through a job.
        self.drop_zone.setEnabled(enabled)
        self.mode_selector.setEnabled(enabled)
        self.threshold_control.setEnabled(enabled)

    def save_file(self):
        # Opens a save window when the user clicks "Download"
        if not self.processed_file_path:
            return
        is_gif = self.processed_file_path.lower().endswith(".gif")
        default_name = "iErase_output.gif" if is_gif else "iErase_output.png"
        file_filter = "GIF Animation (*.gif)" if is_gif else "PNG Image (*.png)"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Clean File",
            default_name,
            file_filter,
        )
        if save_path:
            try:
                shutil.copy2(self.processed_file_path, save_path)
                print("Saved to:", save_path)
            except OSError as error:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Could not save the finished file:\n{error}",
                )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize the falling petals layer whenever the window changes size
        if hasattr(self, "petal_overlay"):
            self.petal_overlay.resize(self.centralWidget().size())

    def load_picture(self, path: str, height: int) -> QLabel:
        # Loads an image, trims empty clear space around it, and scales it cleanly
        label = QLabel()
        label.setContentsMargins(0, 0, 0, 0)
        picture_path = bundled_path(path)

        try:
            pil_img = Image.open(picture_path).convert("RGBA")
            bbox = pil_img.getbbox()
            if bbox:
                pil_img = pil_img.crop(bbox)
            data = pil_img.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
        except Exception:
            pixmap = QPixmap(str(picture_path))

        if not pixmap.isNull():
            label.setPixmap(pixmap.scaledToHeight(height, Qt.SmoothTransformation))
        else:
            label.setText(f"[{path}]")
            label.setStyleSheet("color: #9E7B88; font-size: 12px;")
        return label

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IEraseApp()
    window.show()
    sys.exit(app.exec())
