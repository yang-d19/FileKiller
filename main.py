import argparse
import math
import sys
import os
import winreg

# The PyQt6 Windows wheel exposes both FFmpeg and Windows Media Foundation
# backends, but its FFmpeg plugin may be installed without the matching FFmpeg
# DLLs.  Qt otherwise picks that unusable backend and QMediaPlayer stays silent.
# Select the native Windows backend before importing QtMultimedia.
if sys.platform == "win32":
    os.environ["QT_MEDIA_BACKEND"] = "windows"

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, pyqtSignal, QUrl, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QColor, QTransform, QImage, QPainterPath, QCursor, QPen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from resource_config import CONFIG_ENV_VAR, ResourceConfig, ResourceConfigError

COLS = 5
ROWS = 3

def register_context_menu(config_path=None):
    try:
        config_argument = f' --config "{os.path.abspath(config_path)}"' if config_path else ""
        exe_path = sys.executable
        if not exe_path.lower().endswith('.exe') or 'python' in exe_path.lower():
            # If running from python script, use the old command
            exe_path = sys.executable
            script_path = os.path.abspath(__file__)
            command_str = f'"{exe_path}" "{script_path}"{config_argument} "%1"'
            icon_str = "shell32.dll,32"
        else:
            command_str = f'"{exe_path}"{config_argument} "%1"'
            icon_str = f'"{exe_path}",0'
            
        key_path = r"Software\Classes\*\shell\SummonMonster"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValue(key, "", winreg.REG_SZ, "召唤大将怪兽摧毁")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_str)
        winreg.CloseKey(key)
        
        command_key_path = key_path + r"\command"
        command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path)
        winreg.SetValue(command_key, "", winreg.REG_SZ, command_str)
        winreg.CloseKey(command_key)
    except Exception as e:
        print(f"Error registering menu: {e}")

class SpriteAnimator(QLabel):
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

    def load_spritesheet(self, filepath, cols=COLS, rows=ROWS, target_height=250, frame_indices=None):
        if not os.path.exists(filepath):
            print(f"Error: Sprite not found at {filepath}")
            return False
            
        image = QImage(filepath)
        if image.isNull():
            print(f"Error: Failed to load image {filepath}")
            return False
            
        pixmap = QPixmap.fromImage(image)
        
        frame_w = pixmap.width() // cols
        frame_h = pixmap.height() // rows
        
        self.frames = []
        for r in range(rows):
            for c in range(cols):
                frame = pixmap.copy(c * frame_w, r * frame_h, frame_w, frame_h)
                frame = frame.scaledToHeight(target_height, Qt.TransformationMode.SmoothTransformation)
                self.frames.append(frame)
                
        if frame_indices is not None:
            self.frames = [self.frames[i] for i in frame_indices if i < len(self.frames)]

        if not self.frames:
            print(f"Error: Sprite configuration selected no frames from {filepath}")
            return False

        if self.frames:
            self.resize(self.frames[0].size())
        return True

    def set_flip(self, flip):
        self.flip_horizontal = flip
        self._update_frame()

    def play(self, fps=8, loop=True):
        self.loop = loop
        self.current_frame = self.start_frame % len(self.frames) if self.frames else 0
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
            frame = frame.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(frame)


from PyQt6.QtGui import QPainterPath

class BubbleWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 15) # Leave space at bottom for the tail
        self.lbl_text = QLabel(text)
        
        # Modern Sleek UI Design for text
        style = """
            QLabel {
                color: #1c1c1e; 
                padding: 15px 30px; 
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
                font-size: 20px; 
                font-weight: 600;
            }
        """
        self.lbl_text.setStyleSheet(style)
        
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_text)
        self.setLayout(layout)
        
        # Soft realistic modern shadow on the whole widget
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 240))
        
        rect = self.rect()
        
        # Bubble body
        path = QPainterPath()
        path.addRoundedRect(0, 0, float(rect.width()), float(rect.height() - 15), 20.0, 20.0)
        
        # Dialog Tail pointing to the monster (bottom middle)
        tail = QPainterPath()
        tail.moveTo(float(rect.width()) / 2 - 15, float(rect.height() - 15))
        tail.lineTo(float(rect.width()) / 2, float(rect.height()))
        tail.lineTo(float(rect.width()) / 2 + 15, float(rect.height() - 15))
        path.addPath(tail)
        
        painter.drawPath(path)

class ChoicesWidget(QWidget):
    choiceMade = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        self.btn1 = QPushButton("是的")
        self.btn2 = QPushButton("嘤嘤嘤就是这个")
        
        # Modern Sleek UI Design
        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 240); 
                color: #1c1c1e; 
                border: 1px solid #e5e5ea; 
                border-radius: 18px; 
                padding: 12px 25px; 
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
                font-size: 16px; 
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #007aff;
                color: #ffffff;
                border: 1px solid #007aff;
            }
            QPushButton:pressed {
                background-color: #005bb5;
                color: #ffffff;
            }
        """
        self.btn1.setStyleSheet(btn_style)
        self.btn2.setStyleSheet(btn_style)
        
        # Add soft shadows to buttons
        shadow1 = QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(15)
        shadow1.setOffset(0, 5)
        shadow1.setColor(QColor(0, 0, 0, 30))
        self.btn1.setGraphicsEffect(shadow1)

        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(15)
        shadow2.setOffset(0, 5)
        shadow2.setColor(QColor(0, 0, 0, 30))
        self.btn2.setGraphicsEffect(shadow2)
        
        self.btn1.clicked.connect(self.on_click)
        self.btn2.clicked.connect(self.on_click)
        
        layout.addWidget(self.btn1)
        layout.addWidget(self.btn2)
        self.setLayout(layout)

    def on_click(self):
        self.hide()
        self.choiceMade.emit()
        

class MonsterDeleter(QWidget):
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
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.animator = SpriteAnimator(self)
        self.animator.hide()
        
        self.explosion_animator = SpriteAnimator(self)
        self.explosion_animator.hide()

        self.below_target_animators = []
        self.orbit_labels = []
        self.orbit_angle = 0.0
        self.orbit_timer = QTimer(self)
        self.orbit_timer.timeout.connect(self.update_satellite_orbit)
        
        self.bubble = BubbleWidget("喂，是这个吗？")
        self.choices = ChoicesWidget()
        
        self.init_audio()
        
        # Always launch the sniper targeting UI for interactive aiming
        self.init_targeting_ui()

    @pyqtProperty(float)
    def bg_opacity(self):
        return self._bg_opacity
        
    @bg_opacity.setter
    def bg_opacity(self, value):
        self._bg_opacity = value
        self.update()

    def init_audio(self):
        # Background Music
        bgm = self.resources.audio("bgm")
        self.bgm_player = QMediaPlayer()
        self.bgm_audio = QAudioOutput()
        self.bgm_player.setAudioOutput(self.bgm_audio)
        self.bgm_player.setSource(QUrl.fromLocalFile(bgm["path"]))
        self.bgm_audio.setVolume(bgm["volume"])
        self.bgm_player.mediaStatusChanged.connect(self.loop_bgm)
        
        # Sound Effects
        voice = self.resources.audio("voice")
        self.sfx_player = QMediaPlayer()
        self.sfx_audio = QAudioOutput()
        self.sfx_player.setAudioOutput(self.sfx_audio)
        self.sfx_player.setSource(QUrl.fromLocalFile(voice["path"]))
        self.sfx_audio.setVolume(voice["volume"])
        
        # Explosion Sound
        explosion = self.resources.audio("explosion")
        self.exp_player = QMediaPlayer()
        self.exp_audio = QAudioOutput()
        self.exp_player.setAudioOutput(self.exp_audio)
        self.exp_player.setSource(QUrl.fromLocalFile(explosion["path"]))
        self.exp_audio.setVolume(explosion["volume"])

        # Optional post-destruction voice configured by individual themes.
        self.victory_player = None
        self.victory_audio = None
        victory = self.resources.optional_audio("victory")
        if victory:
            self.victory_player = QMediaPlayer()
            self.victory_audio = QAudioOutput()
            self.victory_player.setAudioOutput(self.victory_audio)
            self.victory_player.setSource(QUrl.fromLocalFile(victory["path"]))
            self.victory_audio.setVolume(victory["volume"])

    def load_sprite(self, animator, name):
        spec = self.resources.sprite(name)
        return self.load_sprite_spec(animator, spec, name)

    def load_sprite_spec(self, animator, spec, label):
        fps = spec.pop("fps")
        filepath = spec.pop("path")
        animator.start_frame = spec.pop("start_frame", 0)
        animator.position_offset_y = spec.pop("offset_y", 0)
        if not animator.load_spritesheet(filepath, **spec):
            raise ResourceConfigError(f"Unable to load sprite resource: {label}")
        return fps

    def loop_bgm(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bgm_player.setPosition(0)
            self.bgm_player.play()

    def init_targeting_ui(self):
        # Create a custom red sniper cursor
        cursor_size = 40
        cursor_pixmap = QPixmap(cursor_size, cursor_size)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(255, 0, 0)) # Red color
        pen.setWidth(2)
        painter.setPen(pen)
        
        center = cursor_size // 2
        radius = 12
        # Draw outer circle
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        
        # Draw crosshairs
        painter.drawLine(center, 0, center, center - 4) # Top
        painter.drawLine(center, center + 4, center, cursor_size) # Bottom
        painter.drawLine(0, center, center - 4, center) # Left
        painter.drawLine(center + 4, center, cursor_size, center) # Right
        
        painter.end()
        
        self.setCursor(QCursor(cursor_pixmap, center, center))
        
        # Start fade in
        self.fade_in_anim = QPropertyAnimation(self, b"bg_opacity")
        self.fade_in_anim.setDuration(800)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(0.35) # Reduced opacity
        self.fade_in_anim.start()
        
    def paintEvent(self, event):
        if self._bg_opacity > 0.01:
            painter = QPainter(self)

            # Draw the background selected by the active resource configuration.
            painter.setOpacity(self._bg_opacity) # Animated opacity
            scaled_img = self.background_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled_img.width()) // 2
            y = (self.height() - scaled_img.height()) // 2
            painter.drawImage(x, y, scaled_img)
                
            # Scale text opacity relative to bg_opacity max (0.35)
            text_opacity = min(1.0, self._bg_opacity / 0.35)
            painter.setOpacity(text_opacity)
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(30)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请选择你要摧毁的文件")

    def mousePressEvent(self, event):
        if not self.monster_sequence_started and event.button() == Qt.MouseButton.LeftButton:
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

    def init_monster_sequence(self):
        self.start_phase1_walk()

    def start_satellite_orbit(self):
        effect = self.resources.orbit_effect()
        if not effect or self.target_pos is None:
            return

        self.stop_satellite_orbit()
        source = QPixmap(effect["path"])
        if source.isNull():
            raise ResourceConfigError(
                f"Unable to load orbit resource: {effect['path']}"
            )

        sprite = source.scaledToWidth(
            effect["target_width"], Qt.TransformationMode.SmoothTransformation
        )
        self.orbit_effect_spec = effect
        self.orbit_angle = 0.0
        for _index in range(effect["count"]):
            label = QLabel(self)
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            label.setPixmap(sprite)
            label.resize(sprite.size())
            label.show()
            self.orbit_labels.append(label)

        self.update_satellite_orbit()
        self.orbit_timer.start(max(1, 1000 // effect["fps"]))

    def update_satellite_orbit(self):
        if not self.orbit_labels or self.target_pos is None:
            return

        effect = self.orbit_effect_spec
        phase_step = 360.0 / len(self.orbit_labels)
        for index, label in enumerate(self.orbit_labels):
            angle = math.radians(self.orbit_angle + index * phase_step)
            center_x = self.target_pos.x() + math.cos(angle) * effect["radius_x"]
            center_y = self.target_pos.y() + math.sin(angle) * effect["radius_y"]
            label.move(
                round(center_x - label.width() / 2),
                round(center_y - label.height() / 2),
            )
            label.raise_()

        self.orbit_angle = (
            self.orbit_angle + effect["speed_dps"] / effect["fps"]
        ) % 360.0

    def stop_satellite_orbit(self):
        self.orbit_timer.stop()
        for label in self.orbit_labels:
            label.hide()
            label.deleteLater()
        self.orbit_labels.clear()

    def start_phase1_walk(self):
        
        # Start playing BGM here
        self.bgm_player.play()
        self.start_below_target_animations()
        
        fps = self.load_sprite(self.animator, "walk")
        
        screen = QApplication.primaryScreen().geometry()
        start_x = -self.animator.width()
        start_y = (
            self.target_pos.y()
            - self.animator.height() // 2
            + 50
            + self.animator.position_offset_y
        )
        
        self.from_right = False
        self.animator.set_flip(False) 
            
        self.animator.move(start_x, start_y)
        self.animator.show()
        self.animator.play(fps=fps, loop=True)
        
        self.move_anim = QPropertyAnimation(self.animator, b"pos")
        self.move_anim.setDuration(4500) # Slower walking speed
        
        # Move pet left so the finger hits the file exactly
        end_x = self.target_pos.x() - self.animator.width() - 30

        self.move_anim.setStartValue(QPoint(start_x, start_y))
        self.move_anim.setEndValue(QPoint(end_x, start_y))
        self.move_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.move_anim.finished.connect(self.start_phase2_point)
        self.move_anim.start()

    def start_phase2_point(self):
        # Play SFX once when pointing animation starts
        self.sfx_player.play()
        
        # Phase 2: Pointing (Play ONCE using the frames selected by the skin.)
        fps = self.load_sprite(self.animator, "point")
        
        try:
            self.animator.animationFinished.disconnect()
        except TypeError:
            pass
            
        self.animator.animationFinished.connect(self.show_dialog)
        self.animator.play(fps=fps, loop=False)

    def show_dialog(self):
        try:
            self.animator.animationFinished.disconnect()
        except TypeError:
            pass
            
        global_pos = self.mapToGlobal(self.animator.pos())
        
        bubble_x = global_pos.x() + (self.animator.width() // 2) - 80
        bubble_y = global_pos.y() - 60 # Moved bubble down
        self.bubble.move(bubble_x, bubble_y)
        self.bubble.show()

        choices_x = global_pos.x() + (self.animator.width() // 2) - 130
        choices_y = global_pos.y() + self.animator.height() - 20 # Moved choices down
        self.choices.move(choices_x, choices_y)
        
        try:
            self.choices.choiceMade.disconnect()
        except TypeError:
            pass
            
        self.choices.choiceMade.connect(self.start_phase3_kick)
        self.choices.show()

    def start_phase3_kick(self):
        self.bubble.hide()
        
        try:
            self.animator.animationFinished.disconnect()
            self.animator.frameChanged.disconnect()
        except TypeError:
            pass
            
        fps = self.load_sprite(self.animator, "kick")
        self.animator.animationFinished.connect(self.on_kick_finished)
        self.animator.frameChanged.connect(self.on_kick_frame)
        self.animator.play(fps=fps, loop=False)

    def on_kick_frame(self, frame_idx):
        # Trigger explosion precisely on the 6th frame (index 5)
        if frame_idx == 5:
            self.trigger_explosion()

    def trigger_explosion(self):
        self.stop_satellite_orbit()

        # Play explosion sound
        self.exp_player.play()
        
        fps = self.load_sprite(self.explosion_animator, "explosion")
        
        # Center explosion slightly higher to cover the file icon properly
        exp_x = self.target_pos.x() - self.explosion_animator.width() // 2
        exp_y = self.target_pos.y() - self.explosion_animator.height() // 2 - 40
        self.explosion_animator.move(exp_x, exp_y)
        self.explosion_animator.show()
        
        try:
            self.explosion_animator.animationFinished.disconnect()
        except TypeError:
            pass
            
        self.explosion_animator.animationFinished.connect(self.explosion_animator.hide)
        self.explosion_animator.play(fps=fps, loop=False)

        # We can trigger the file deletion here to perfectly sync with explosion
        if self.delete_target_file():
            self.play_victory_voice()

    def play_victory_voice(self):
        if self.victory_player is not None:
            self.victory_player.setPosition(0)
            self.victory_player.play()

    def start_below_target_animations(self):
        group = self.resources.animation_group("below_target")
        if not group:
            return

        self.stop_below_target_animations()
        loaded = []
        for index, spec in enumerate(group["items"]):
            animator = SpriteAnimator(self)
            fps = self.load_sprite_spec(
                animator, spec, f"animations.below_target[{index}]"
            )
            loaded.append((animator, fps))

        spacing = group["spacing"]
        total_width = sum(animator.width() for animator, _fps in loaded)
        total_width += spacing * (len(loaded) - 1)
        max_height = max(animator.height() for animator, _fps in loaded)

        desired_x = self.target_pos.x() - total_width // 2
        start_x = max(0, min(desired_x, max(0, self.width() - total_width)))
        desired_y = self.target_pos.y() + group["offset_y"]
        top_y = max(0, min(desired_y, max(0, self.height() - max_height)))

        current_x = start_x
        for animator, fps in loaded:
            animator.move(current_x, top_y + max_height - animator.height())
            animator.show()
            animator.play(fps=fps, loop=True)
            self.below_target_animators.append(animator)
            current_x += animator.width() + spacing

        if group["duration_ms"] > 0:
            QTimer.singleShot(
                group["duration_ms"], self.stop_below_target_animations
            )

    def stop_below_target_animations(self):
        for animator in self.below_target_animators:
            animator.stop()
            animator.hide()
            animator.deleteLater()
        self.below_target_animators.clear()

    def delete_target_file(self):
        try:
            from send2trash import send2trash
            if self.target_file and os.path.exists(self.target_file):
                send2trash(self.target_file)
                print(f"Moved to trash: {self.target_file}")
                return True
        except Exception as e:
            print(f"Error: {e}")
        return False

    def on_kick_finished(self):
        try:
            self.animator.animationFinished.disconnect()
            self.animator.frameChanged.disconnect()
        except TypeError:
            pass
            
        self.start_phase4_leo()

    def start_phase4_leo(self):
        fps = self.load_sprite(self.animator, "arrival")
        self.animator.animationFinished.connect(self.start_phase5_fly)
        self.animator.play(fps=fps, loop=False)

    def start_phase5_fly(self):
        try:
            self.animator.animationFinished.disconnect()
        except TypeError:
            pass
            
        fps = self.load_sprite(self.animator, "departure")
        self.animator.play(fps=fps, loop=True)
        
        screen = QApplication.primaryScreen().geometry()
        self.move_anim2 = QPropertyAnimation(self.animator, b"pos")
        self.move_anim2.setDuration(2000)
        self.move_anim2.setStartValue(self.animator.pos())
        
        end_x = screen.width() + 200
        end_y = self.animator.pos().y()
            
        self.move_anim2.setEndValue(QPoint(end_x, end_y))
        self.move_anim2.setEasingCurve(QEasingCurve.Type.InQuad)
        self.move_anim2.finished.connect(self.on_app_exit)
        self.move_anim2.start()

    def on_app_exit(self):
        # Explicitly stop multimedia to free resources and stop background audio
        self.stop_satellite_orbit()
        self.stop_below_target_animations()
        self.bgm_player.stop()
        self.sfx_player.stop()
        self.exp_player.stop()
        if self.victory_player is not None:
            self.victory_player.stop()
        self.close()
        QApplication.quit()
        sys.exit(0)


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="Desktop Monster Deleter")
    parser.add_argument(
        "--config",
        help=(
            "Resource configuration JSON. Relative resource paths inside it are "
            "resolved from the configuration file's directory."
        ),
    )
    parser.add_argument("target", nargs="?", help="File to move to the recycle bin")
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_arguments()
    config_override = args.config or os.environ.get(CONFIG_ENV_VAR)
    try:
        resources = ResourceConfig.load(config_override)
    except ResourceConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    register_context_menu(resources.source_path if config_override else None)

    app = QApplication([sys.argv[0]])
    ex = MonsterDeleter(args.target, resources)
    ex.show()
    sys.exit(app.exec())
