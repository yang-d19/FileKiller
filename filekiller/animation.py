"""Sprite-sheet playback and resource-to-widget loading helpers."""

from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtProperty, pyqtSignal
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
        self.move_duration_ms = 2000
        self.move_wave_cycles = 0
        self.move_wave_strength = 0.0
        self.stabilize_x = False
        self._frame_anchors_x = []
        self._stabilization_anchor_x = None
        self._motion_position = QPoint(self.pos())

    def load_spritesheet(
        self,
        filepath,
        cols=DEFAULT_COLS,
        rows=DEFAULT_ROWS,
        target_height=250,
        frame_indices=None,
        stabilize_x=False,
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

        self._configure_horizontal_stabilization(stabilize_x)
        self.resize(self.frames[0].size())
        return True

    def _configure_horizontal_stabilization(self, enabled):
        """Offset visual frames around a stable anchor without blocking travel."""

        was_enabled = self.stabilize_x
        if enabled:
            self._frame_anchors_x = [
                self._visible_upper_anchor_x(frame) for frame in self.frames
            ]
            if not was_enabled or self._stabilization_anchor_x is None:
                self._motion_position = QPoint(self.pos())
                self._stabilization_anchor_x = self._frame_anchors_x[0]
        else:
            if was_enabled:
                self.move(self._motion_position)
            self._frame_anchors_x = []
            self._stabilization_anchor_x = None

        self.stabilize_x = enabled

    @pyqtProperty(QPoint)
    def motion_position(self):
        """Logical travel position before per-frame stabilization is applied."""

        return QPoint(self._motion_position if self.stabilize_x else self.pos())

    @motion_position.setter
    def motion_position(self, position):
        self._motion_position = QPoint(position)
        self._apply_stabilized_position()

    def _apply_stabilized_position(self, anchor_x=None, frame_width=None):
        if not self.stabilize_x or self._stabilization_anchor_x is None:
            self.move(self._motion_position)
            return

        if anchor_x is None:
            anchor_x = self._frame_anchors_x[self.current_frame]
            frame_width = self.frames[self.current_frame].width()
        if self.flip_horizontal:
            anchor_x = frame_width - 1 - anchor_x

        frame_offset_x = round(self._stabilization_anchor_x - anchor_x)
        self.move(
            self._motion_position.x() + frame_offset_x,
            self._motion_position.y(),
        )

    @staticmethod
    def _visible_upper_anchor_x(frame, alpha_threshold=24, upper_fraction=0.42):
        """Return the horizontal median of the visible upper part of a frame."""

        image = frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width = image.width()
        height = image.height()
        data = image.constBits()
        data.setsize(image.sizeInBytes())
        alpha = bytes(data)[3::4]
        visible_pixels = [
            index for index, value in enumerate(alpha) if value > alpha_threshold
        ]

        if not visible_pixels:
            return (width - 1) / 2

        top = visible_pixels[0] // width
        bottom = visible_pixels[-1] // width
        upper_limit = top + (bottom - top) * upper_fraction
        upper_end = (int(upper_limit) + 1) * width
        counts = [0] * width
        total = 0
        for index in visible_pixels:
            if index >= upper_end:
                break
            counts[index % width] += 1
            total += 1

        midpoint = (total - 1) / 2
        seen = 0
        for x, count in enumerate(counts):
            seen += count
            if seen > midpoint:
                return x
        return (width - 1) / 2

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
        anchor_x = None
        if self.stabilize_x and self._stabilization_anchor_x is not None:
            anchor_x = self._frame_anchors_x[self.current_frame]
        if self.flip_horizontal:
            transform = QTransform().scale(-1, 1)
            frame = frame.transformed(
                transform, Qt.TransformationMode.SmoothTransformation
            )
        if anchor_x is not None:
            self._apply_stabilized_position(anchor_x, frame.width())
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
        animator.move_duration_ms = options.pop("move_duration_ms", 2000)
        animator.move_wave_cycles = options.pop("move_wave_cycles", 0)
        animator.move_wave_strength = options.pop("move_wave_strength", 0.0)
        if not animator.load_spritesheet(filepath, **options):
            raise ResourceConfigError(f"Unable to load sprite resource: {label}")
        return fps
