#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from PySide6.QtCore import QUrl, QObject
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class SoundPlayer(QObject):
    def __init__(self, logger=None):
        super().__init__()
        self.player = None
        self.audio_output = None
        self.current_type = None
        self.current_path = None
        self.logger = logger

    def _normalize_volume(self, volume):
        try:
            volume = int(volume)
        except (TypeError, ValueError):
            volume = 100
        return max(0, min(100, volume))

    def _play_file(self, audio_path, sound_type, volume, log_category):
        """Запускает аудиофайл через QtMultimedia с изменяемой на лету громкостью."""
        if not audio_path or not Path(audio_path).exists():
            if self.logger:
                self.logger.log_event("error", f"Audio file not found: {audio_path}")
            return False

        try:
            volume = self._normalize_volume(volume)
            self.stop_all()

            # Отключаем сигналы и освобождаем старые Qt-объекты перед созданием новых
            if self.player is not None:
                try:
                    self.player.mediaStatusChanged.disconnect()
                    self.player.playbackStateChanged.disconnect()
                except RuntimeError:
                    pass
                self.player.deleteLater()
            if self.audio_output is not None:
                self.audio_output.deleteLater()

            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(volume / 100.0)

            self.player = QMediaPlayer()
            self.player.setAudioOutput(self.audio_output)
            self.player.setSource(QUrl.fromLocalFile(str(Path(audio_path).resolve())))
            
            # Подключаем сигналы для автоматической очистки ресурсов
            self.player.mediaStatusChanged.connect(self._on_media_status_changed)
            self.player.playbackStateChanged.connect(self._on_playback_state_changed)

            self.current_type = sound_type
            self.current_path = str(audio_path)
            self.player.play()

            if self.logger:
                self.logger.log_event(
                    log_category,
                    f"Played {sound_type}: {Path(audio_path).name} (volume: {volume}%)",
                )
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_event("error", f"Error playing {sound_type}: {e}")
            print(f"Error playing audio: {e}")
            self._clear_current()
            return False

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._clear_current()

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._clear_current()

    def _clear_current(self):
        if self.current_type is None and self.current_path is None:
            return
        self.current_type = None
        self.current_path = None
        # Очищает текущее состояние, но НЕ вызывает deleteLater() сразу.
        #
        # deleteLater() должен вызываться только при закрытии приложения,
        # чтобы избежать проблем с повторным использованием объектов.
        # Не обнуляем player и audio_output здесь - они нужны для проверки состояния

    def play(self, sound_path, sound_type="auto", volume=100):
        """Воспроизведение звука с поддержкой громкости.

        Args:
            sound_path: Путь к аудиофайлу
            sound_type: Тип звука (start, end, anthem, announcement)
            volume: Громкость от 0 до 100
        """
        return self._play_file(sound_path, sound_type, volume, "bell")

    def play_music(self, track_path, volume=50):
        """Воспроизведение музыки через тот же проигрыватель с поддержкой громкости."""
        return self._play_file(track_path, "music", volume, "music")

    def set_volume(self, volume):
        """Меняет громкость текущего воспроизведения без перезапуска файла."""
        if self.audio_output:
            volume = self._normalize_volume(volume)
            self.audio_output.setVolume(volume / 100.0)
            if self.logger:
                self.logger.log_event("volume", f"Volume changed for {self.current_type}: {volume}%")
            return True
        return False

    def is_playing(self, sound_type=None):
        """Проверяет, запущено ли сейчас воспроизведение указанного типа или любого звука."""
        if not self.player:
            return False
        actually_playing = (
            self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        )
        if not actually_playing:
            return False
        if sound_type is None:
            return True
        return self.current_type == sound_type

    def stop_all(self):
        """Остановка любого воспроизведения (звонка, музыки, гимна или объявления)."""
        if self.player:
            self.player.stop()
        self.current_type = None
        self.current_path = None

    def cleanup(self):
        """Корректно освобождает ресурсы Qt-объектов.
        
        Должен вызываться только при закрытии приложения.
        """
        if self.player:
            self.player.stop()
            self.player.deleteLater()
            self.player = None
        
        if self.audio_output:
            self.audio_output.deleteLater()
            self.audio_output = None
        
        self.current_type = None
        self.current_path = None
