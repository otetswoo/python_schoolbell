#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import subprocess
import time
import os
from pathlib import Path
import datetime


class SoundPlayer:
    def __init__(self, logger=None):
        self.current_process = None
        self.logger = logger
    
    def play(self, sound_path, sound_type="auto", volume=100):
        """Воспроизведение звука с поддержкой громкости
        
        Args:
            sound_path: Путь к аудиофайлу
            sound_type: Тип звука (start, end, anthem)
            volume: Громкость от 0 до 100
        """
        if not sound_path or not Path(sound_path).exists():
            if self.logger:
                self.logger.log_event("error", f"Sound file not found: {sound_path}")
            return False
        
        try:
            ext = Path(sound_path).suffix.lower()
            
            # Преобразуем громкость в формат ffplay (0-65535)
            ffplay_volume = int((volume / 100.0) * 65535)
            
            if platform.system() == "Windows":
                try:
                    from PySide6.QtMultimedia import QSound
                    QSound.play(str(sound_path))
                    if self.logger:
                        self.logger.log_event("bell", f"Played {sound_type}: {Path(sound_path).name} (volume: {volume}%)")
                except:
                    self.current_process = subprocess.Popen(
                        ["powershell", "-Command", f'(New-Object Media.SoundPlayer "{sound_path}").PlaySync()'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    if self.logger:
                        self.logger.log_event("bell", f"Played {sound_type}: {Path(sound_path).name}")
            else:
                if ext == ".wav":
                    self.current_process = subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac", ".m4a"):
                    # Используем ffplay с параметром громкости
                    self.current_process = subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", 
                         "-volume", str(ffplay_volume), str(sound_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    self.current_process = subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if self.logger:
                    self.logger.log_event("bell", f"Played {sound_type}: {Path(sound_path).name} (volume: {volume}%)")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event("error", f"Error playing {sound_type}: {e}")
            print(f"Error playing sound: {e}")
            return False
    
    def play_music(self, track_path, volume=50):
        """Воспроизведение музыки через тот же процесс с поддержкой громкости
        
        Args:
            track_path: Путь к аудиофайлу
            volume: Громкость от 0 до 100
        """
        if not track_path or not Path(track_path).exists():
            if self.logger:
                self.logger.log_event("error", f"Music file not found: {track_path}")
            return False
        
        try:
            ext = Path(track_path).suffix.lower()
            
            # Преобразуем громкость в формат ffplay (0-65535)
            ffplay_volume = int((volume / 100.0) * 65535)
            
            if platform.system() == "Windows":
                os.startfile(str(track_path))
                if self.logger:
                    self.logger.log_event("music", f"Played music: {Path(track_path).name}")
            else:
                if ext == ".wav":
                    self.current_process = subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac", ".m4a"):
                    self.current_process = subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                         "-volume", str(ffplay_volume), str(track_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    self.current_process = subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if self.logger:
                    self.logger.log_event("music", f"Played music: {Path(track_path).name} (volume: {volume}%)")
            
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_event("error", f"Error playing music: {e}")
            print(f"Error playing music: {e}")
            return False
    
    def stop_all(self):
        """Остановка любого воспроизведения (звонка или музыки)"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=2)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
            finally:
                self.current_process = None
