"""Reusable visual-effect controllers hosted by the main overlay window."""

import math

from PyQt6.QtCore import QElapsedTimer, QObject, QPoint, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel

from .animation import SpriteAnimator
from .config import ResourceConfigError


class OrbitEffectController(QObject):
    """Animate configured images on an elliptical orbit around a target."""

    def __init__(self, host, parent=None):
        super().__init__(parent or host)
        self.host = host
        self.labels = []
        self.target_pos = None
        self.spec = None
        self.angle = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions)

    def start(self, target_pos, spec):
        if not spec or target_pos is None:
            return

        self.stop()
        source = QPixmap(spec["path"])
        if source.isNull():
            raise ResourceConfigError(
                f"Unable to load orbit resource: {spec['path']}"
            )

        sprite = source.scaledToWidth(
            spec["target_width"], Qt.TransformationMode.SmoothTransformation
        )
        self.target_pos = target_pos
        self.spec = spec
        self.angle = 0.0
        for _ in range(spec["count"]):
            label = QLabel(self.host)
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            label.setPixmap(sprite)
            label.resize(sprite.size())
            label.show()
            self.labels.append(label)

        self.update_positions()
        self.timer.start(max(1, 1000 // spec["fps"]))

    def update_positions(self):
        if not self.labels or self.target_pos is None or self.spec is None:
            return

        phase_step = 360.0 / len(self.labels)
        for index, label in enumerate(self.labels):
            angle = math.radians(self.angle + index * phase_step)
            center_x = (
                self.target_pos.x() + math.cos(angle) * self.spec["radius_x"]
            )
            center_y = (
                self.target_pos.y() + math.sin(angle) * self.spec["radius_y"]
            )
            label.move(
                round(center_x - label.width() / 2),
                round(center_y - label.height() / 2),
            )
            label.raise_()

        self.angle = (
            self.angle + self.spec["speed_dps"] / self.spec["fps"]
        ) % 360.0

    def stop(self):
        self.timer.stop()
        for label in self.labels:
            label.hide()
            label.deleteLater()
        self.labels.clear()


class AnimationGroupController(QObject):
    """Lay out and play a configured sprite group below the selected target."""

    def __init__(self, host, sprite_loader, parent=None):
        super().__init__(parent or host)
        self.host = host
        self.sprite_loader = sprite_loader
        self.animators = []
        self.base_positions = []
        self.group = None
        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(self.stop)
        self.bounce_clock = QElapsedTimer()
        self.bounce_timer = QTimer(self)
        self.bounce_timer.timeout.connect(self.update_bounce_positions)

    def start(self, target_pos, group):
        if not group or target_pos is None:
            return

        self.stop()
        self.group = group
        loaded = []
        for index, spec in enumerate(group["items"]):
            animator = SpriteAnimator(self.host)
            fps = self.sprite_loader.load_spec(
                animator, spec, f"animations.below_target[{index}]"
            )
            loaded.append((animator, fps))

        spacing = group["spacing"]
        total_width = sum(animator.width() for animator, _ in loaded)
        total_width += spacing * (len(loaded) - 1)
        max_height = max(animator.height() for animator, _ in loaded)

        desired_x = target_pos.x() - total_width // 2
        start_x = max(0, min(desired_x, max(0, self.host.width() - total_width)))
        desired_y = target_pos.y() + group["offset_y"]
        top_y = max(0, min(desired_y, max(0, self.host.height() - max_height)))

        current_x = start_x
        for animator, fps in loaded:
            base_position = QPoint(
                current_x, top_y + max_height - animator.height()
            )
            animator.move(base_position)
            animator.show()
            animator.play(fps=fps, loop=True)
            self.animators.append(animator)
            self.base_positions.append(base_position)
            current_x += animator.width() + spacing

        if group["bounce_height"] > 0:
            self.bounce_clock.start()
            self.update_bounce_positions()
            self.bounce_timer.start(max(1, 1000 // group["bounce_fps"]))

        if group["duration_ms"] > 0:
            self.stop_timer.start(group["duration_ms"])

    def update_bounce_positions(self):
        if not self.animators or self.group is None:
            return
        self._apply_bounce(self.bounce_clock.elapsed())

    def _apply_bounce(self, elapsed_ms):
        """Move the group in a staggered upward-only jumping wave."""

        period_ms = self.group["bounce_period_ms"]
        height = self.group["bounce_height"]
        phase_step = 2 * math.pi / len(self.animators)
        time_phase = 2 * math.pi * elapsed_ms / period_ms

        for index, (animator, base_position) in enumerate(
            zip(self.animators, self.base_positions)
        ):
            jump = height * max(0.0, math.sin(time_phase + index * phase_step))
            animator.move(base_position.x(), max(0, base_position.y() - round(jump)))

    def stop(self):
        self.stop_timer.stop()
        self.bounce_timer.stop()
        for animator in self.animators:
            animator.stop()
            animator.hide()
            animator.deleteLater()
        self.animators.clear()
        self.base_positions.clear()
        self.group = None
