"""Sprite-sheet playback and resource-to-widget loading helpers."""

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QTransform
from PyQt6.QtWidgets import QLabel

from .config import ResourceConfigError


DEFAULT_COLS = 5
DEFAULT_ROWS = 3


class SpriteAnimator(QLabel):
    """A QLabel that plays equally sized cells from a sprite sheet."""

    animationFinished = pyqtSignal()
    frameChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.loop = True
        self.flip_horizontal = False
        self.is_playing = False
        self.start_frame = 0
        self.position_offset_y = 0

    def load_spritesheet(
        self,
        filepath,
        cols=DEFAULT_COLS,
        rows=DEFAULT_ROWS,
        target_height=250,
        frame_indices=None,
    ):
        path = Path(filepath)
        if not path.is_file():
            print(f"Error: Sprite not found at {path}")
            return False

        image = QImage(str(path))
        if image.isNull():
            print(f"Error: Failed to load image {path}")
            return False

        pixmap = QPixmap.fromImage(image)
        frame_width = pixmap.width() // cols
        frame_height = pixmap.height() // rows

        self.frames = []
        for row in range(rows):
            for col in range(cols):
                frame = pixmap.copy(
                    col * frame_width, row * frame_height, frame_width, frame_height
                )
                frame = frame.scaledToHeight(
                    target_height, Qt.TransformationMode.SmoothTransformation
                )
                self.frames.append(frame)

        if frame_indices is not None:
            self.frames = [
                self.frames[index]
                for index in frame_indices
                if index < len(self.frames)
            ]

        if not self.frames:
            print(f"Error: Sprite configuration selected no frames from {path}")
            return False

        self.resize(self.frames[0].size())
        return True

    def set_flip(self, flip):
        self.flip_horizontal = flip
        self._update_frame()

    def play(self, fps=8, loop=True):
        if not self.frames:
            return
        self.loop = loop
        self.current_frame = self.start_frame % len(self.frames)
        self.is_playing = True
        self.timer.start(1000 // fps)
        self._update_frame()

    def stop(self):
        self.timer.stop()
        self.is_playing = False

    def next_frame(self):
        if not self.frames:
            return

        self.current_frame += 1
        if self.current_frame >= len(self.frames):
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = len(self.frames) - 1
                self.stop()
                self._update_frame()
                self.frameChanged.emit(self.current_frame)
                self.animationFinished.emit()
                return

        self._update_frame()
        self.frameChanged.emit(self.current_frame)

    def _update_frame(self):
        if not self.frames:
            return
        frame = self.frames[self.current_frame]
        if self.flip_horizontal:
            transform = QTransform().scale(-1, 1)
            frame = frame.transformed(
                transform, Qt.TransformationMode.SmoothTransformation
            )
        self.setPixmap(frame)


class SpriteLoader:
    """Apply validated resource specs to SpriteAnimator instances."""

    def __init__(self, resources):
        self.resources = resources

    def load_named(self, animator, name):
        return self.load_spec(animator, self.resources.sprite(name), name)

    def load_spec(self, animator, spec, label):
        options = dict(spec)
        fps = options.pop("fps")
        filepath = options.pop("path")
        animator.start_frame = options.pop("start_frame", 0)
        animator.position_offset_y = options.pop("offset_y", 0)
        if not animator.load_spritesheet(filepath, **options):
            raise ResourceConfigError(f"Unable to load sprite resource: {label}")
        return fps
