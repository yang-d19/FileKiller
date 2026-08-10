"""Main transparent overlay and the destruction-animation state machine."""

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QCursor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget

from .animation import SpriteAnimator, SpriteLoader
from .config import ResourceConfig, ResourceConfigError
from .effects import AnimationGroupController, OrbitEffectController
from .filesystem import move_to_trash
from .media import AudioController
from .widgets import BubbleWidget, ChoicesWidget


def _disconnect_signal(signal):
    """Disconnect every receiver while tolerating a signal with none."""

    try:
        signal.disconnect()
    except TypeError:
        pass


class FileKillerWindow(QWidget):
    """Coordinate targeting, character phases, effects, audio, and deletion."""

    def __init__(self, target_file, resources=None):
        super().__init__()
        self.target_file = target_file
        self.resources = resources or ResourceConfig.load()
        self.target_pos = None
        self._bg_opacity = 0.0
        self.monster_sequence_started = False

        self.background_image = QImage(self.resources.background_path)
        if self.background_image.isNull():
            raise ResourceConfigError(
                f"Unable to load background image: {self.resources.background_path}"
            )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())

        self.sprite_loader = SpriteLoader(self.resources)
        self.animator = SpriteAnimator(self)
        self.animator.hide()
        self.explosion_animator = SpriteAnimator(self)
        self.explosion_animator.hide()

        self.orbit_effect = OrbitEffectController(self)
        self.orbit_labels = self.orbit_effect.labels
        self.orbit_timer = self.orbit_effect.timer
        self.below_target_effect = AnimationGroupController(
            self, self.sprite_loader
        )
        self.below_target_animators = self.below_target_effect.animators

        self.bubble = BubbleWidget("喂，是这个吗？")
        self.choices = ChoicesWidget()
        self.init_audio()
        self.init_targeting_ui()

    @pyqtProperty(float)
    def bg_opacity(self):
        return self._bg_opacity

    @bg_opacity.setter
    def bg_opacity(self, value):
        self._bg_opacity = value
        self.update()

    @property
    def orbit_angle(self):
        """Compatibility view of the extracted orbit controller state."""

        return self.orbit_effect.angle

    @orbit_angle.setter
    def orbit_angle(self, value):
        self.orbit_effect.angle = value

    @property
    def orbit_effect_spec(self):
        return self.orbit_effect.spec

    @orbit_effect_spec.setter
    def orbit_effect_spec(self, value):
        self.orbit_effect.spec = value

    # ---- Resource and audio compatibility helpers ---------------------

    def init_audio(self):
        """Initialize audio and retain the original public channel names."""

        previous = getattr(self, "audio", None)
        if previous is not None:
            previous.stop_all()
            previous.deleteLater()

        self.audio = AudioController(self.resources, self)
        self.bgm_player = self.audio.bgm_player
        self.bgm_audio = self.audio.bgm_output
        self.sfx_player = self.audio.voice_player
        self.sfx_audio = self.audio.voice_output
        self.exp_player = self.audio.explosion_player
        self.exp_audio = self.audio.explosion_output
        self.victory_player = self.audio.victory_player
        self.victory_audio = self.audio.victory_output

    def load_sprite(self, animator, name):
        return self.sprite_loader.load_named(animator, name)

    def load_sprite_spec(self, animator, spec, label):
        return self.sprite_loader.load_spec(animator, spec, label)

    def loop_bgm(self, status):
        self.audio._loop_bgm(status)

    # ---- Target selection ---------------------------------------------

    def init_targeting_ui(self):
        cursor_size = 40
        cursor_pixmap = QPixmap(cursor_size, cursor_size)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(255, 0, 0))
        pen.setWidth(2)
        painter.setPen(pen)

        center = cursor_size // 2
        radius = 12
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        painter.drawLine(center, 0, center, center - 4)
        painter.drawLine(center, center + 4, center, cursor_size)
        painter.drawLine(0, center, center - 4, center)
        painter.drawLine(center + 4, center, cursor_size, center)
        painter.end()
        self.setCursor(QCursor(cursor_pixmap, center, center))

        self.fade_in_anim = QPropertyAnimation(self, b"bg_opacity")
        self.fade_in_anim.setDuration(800)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(0.35)
        self.fade_in_anim.start()

    def paintEvent(self, event):
        del event
        if self._bg_opacity <= 0.01:
            return

        painter = QPainter(self)
        painter.setOpacity(self._bg_opacity)
        scaled_image = self.background_image.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled_image.width()) // 2
        y = (self.height() - scaled_image.height()) // 2
        painter.drawImage(x, y, scaled_image)

        painter.setOpacity(min(1.0, self._bg_opacity / 0.35))
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(30)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, "请选择你要摧毁的文件"
        )

    def mousePressEvent(self, event):
        if self.monster_sequence_started:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.target_pos = event.pos()
        self.monster_sequence_started = True
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.start_satellite_orbit()

        self.fade_out_anim = QPropertyAnimation(self, b"bg_opacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(self._bg_opacity)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.init_monster_sequence)
        self.fade_out_anim.start()

    # ---- Optional target effects --------------------------------------

    def start_satellite_orbit(self):
        self.orbit_effect.start(self.target_pos, self.resources.orbit_effect())

    def update_satellite_orbit(self):
        self.orbit_effect.update_positions()

    def stop_satellite_orbit(self):
        self.orbit_effect.stop()

    def start_below_target_animations(self):
        group = self.resources.animation_group("below_target")
        self.below_target_effect.start(self.target_pos, group)

    def stop_below_target_animations(self):
        self.below_target_effect.stop()

    # ---- Character phase state machine --------------------------------

    def init_monster_sequence(self):
        self.start_phase1_walk()

    def start_phase1_walk(self):
        self.audio.play_bgm()
        self.start_below_target_animations()
        fps = self.load_sprite(self.animator, "walk")

        start_x = -self.animator.width()
        start_y = (
            self.target_pos.y()
            - self.animator.height() // 2
            + 50
            + self.animator.position_offset_y
        )
        self.animator.set_flip(False)
        self.animator.move(start_x, start_y)
        self.animator.show()
        self.animator.play(fps=fps, loop=True)

        end_x = self.target_pos.x() - self.animator.width() - 30
        self.move_anim = QPropertyAnimation(self.animator, b"pos")
        self.move_anim.setDuration(4500)
        self.move_anim.setStartValue(QPoint(start_x, start_y))
        self.move_anim.setEndValue(QPoint(end_x, start_y))
        self.move_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.move_anim.finished.connect(self.start_phase2_point)
        self.move_anim.start()

    def start_phase2_point(self):
        self.audio.play_voice()
        fps = self.load_sprite(self.animator, "point")
        _disconnect_signal(self.animator.animationFinished)
        self.animator.animationFinished.connect(self.show_dialog)
        self.animator.play(fps=fps, loop=False)

    def show_dialog(self):
        _disconnect_signal(self.animator.animationFinished)
        global_pos = self.mapToGlobal(self.animator.pos())

        bubble_x = global_pos.x() + self.animator.width() // 2 - 80
        bubble_y = global_pos.y() - 60
        self.bubble.move(bubble_x, bubble_y)
        self.bubble.show()

        choices_x = global_pos.x() + self.animator.width() // 2 - 130
        choices_y = global_pos.y() + self.animator.height() - 20
        self.choices.move(choices_x, choices_y)
        _disconnect_signal(self.choices.choiceMade)
        self.choices.choiceMade.connect(self.start_phase3_kick)
        self.choices.show()

    def start_phase3_kick(self):
        self.bubble.hide()
        _disconnect_signal(self.animator.animationFinished)
        _disconnect_signal(self.animator.frameChanged)

        fps = self.load_sprite(self.animator, "kick")
        self.animator.animationFinished.connect(self.on_kick_finished)
        self.animator.frameChanged.connect(self.on_kick_frame)
        self.animator.play(fps=fps, loop=False)

    def on_kick_frame(self, frame_index):
        if frame_index == 5:
            self.trigger_explosion()

    def trigger_explosion(self):
        self.stop_satellite_orbit()
        self.audio.play_explosion()
        fps = self.load_sprite(self.explosion_animator, "explosion")

        explosion_x = self.target_pos.x() - self.explosion_animator.width() // 2
        explosion_y = (
            self.target_pos.y() - self.explosion_animator.height() // 2 - 40
        )
        self.explosion_animator.move(explosion_x, explosion_y)
        self.explosion_animator.show()
        _disconnect_signal(self.explosion_animator.animationFinished)
        self.explosion_animator.animationFinished.connect(
            self.explosion_animator.hide
        )
        self.explosion_animator.play(fps=fps, loop=False)

        if self.delete_target_file():
            self.play_victory_voice()

    def play_victory_voice(self):
        self.audio.play_victory()

    def delete_target_file(self):
        deleted = move_to_trash(self.target_file)
        if deleted:
            print(f"Moved to trash: {self.target_file}")
        return deleted

    def on_kick_finished(self):
        _disconnect_signal(self.animator.animationFinished)
        _disconnect_signal(self.animator.frameChanged)
        self.start_phase4_leo()

    def start_phase4_leo(self):
        fps = self.load_sprite(self.animator, "arrival")
        self.animator.animationFinished.connect(self.start_phase5_fly)
        self.animator.play(fps=fps, loop=False)

    def start_phase5_fly(self):
        _disconnect_signal(self.animator.animationFinished)
        fps = self.load_sprite(self.animator, "departure")
        self.animator.play(fps=fps, loop=True)

        screen = QApplication.primaryScreen().geometry()
        self.move_anim2 = QPropertyAnimation(self.animator, b"pos")
        self.move_anim2.setDuration(2000)
        self.move_anim2.setStartValue(self.animator.pos())
        self.move_anim2.setEndValue(QPoint(screen.width() + 200, self.animator.pos().y()))
        self.move_anim2.setEasingCurve(QEasingCurve.Type.InQuad)
        self.move_anim2.finished.connect(self.on_app_exit)
        self.move_anim2.start()

    # ---- Shutdown ------------------------------------------------------

    def _stop_runtime_resources(self):
        self.stop_satellite_orbit()
        self.stop_below_target_animations()
        self.audio.stop_all()

    def on_app_exit(self):
        self._stop_runtime_resources()
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        self._stop_runtime_resources()
        self.bubble.close()
        self.choices.close()
        super().closeEvent(event)


# The original class name is part of the informal public API and is kept for
# integrations or tests that import it directly.
MonsterDeleter = FileKillerWindow
