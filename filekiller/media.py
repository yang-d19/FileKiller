"""Audio playback channels used by the desktop animation."""

from PyQt6.QtCore import QObject, QUrl

from .runtime import configure_qt_media_backend


# Qt chooses its multimedia backend while QtMultimedia is imported.  Keep this
# call above that import so Windows source checkouts and packaged builds behave
# consistently.
configure_qt_media_backend()

from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer  # noqa: E402


class AudioController(QObject):
    """Own and coordinate the independent audio channels for one window."""

    def __init__(self, resources, parent=None):
        super().__init__(parent)
        self.bgm_player, self.bgm_output = self._create_channel(
            resources.audio("bgm")
        )
        self.voice_player, self.voice_output = self._create_channel(
            resources.audio("voice")
        )
        self.explosion_player, self.explosion_output = self._create_channel(
            resources.audio("explosion")
        )

        victory = resources.optional_audio("victory")
        self.victory_player = None
        self.victory_output = None
        if victory is not None:
            self.victory_player, self.victory_output = self._create_channel(victory)

        self.bgm_player.mediaStatusChanged.connect(self._loop_bgm)

    def _create_channel(self, spec):
        player = QMediaPlayer(self)
        output = QAudioOutput(self)
        player.setAudioOutput(output)
        player.setSource(QUrl.fromLocalFile(spec["path"]))
        output.setVolume(spec["volume"])
        return player, output

    def _loop_bgm(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.bgm_player.setPosition(0)
            self.bgm_player.play()

    def play_bgm(self):
        self.bgm_player.play()

    def play_voice(self):
        self.voice_player.play()

    def play_explosion(self):
        self.explosion_player.play()

    def play_victory(self):
        if self.victory_player is not None:
            self.victory_player.setPosition(0)
            self.victory_player.play()

    def stop_all(self):
        for player in (
            self.bgm_player,
            self.voice_player,
            self.explosion_player,
            self.victory_player,
        ):
            if player is not None:
                player.stop()
