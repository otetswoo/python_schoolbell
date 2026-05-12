#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import subprocess
import time
import os
from pathlib import Path


class SoundPlayer:
    def __init__(self):
        self.current_process = None
    
    def play(self, sound_path, sound_type="auto"):
        if not sound_path or not Path(sound_path).exists():
            return False
        
        # Для ручного воспроизведения (test) убираем кулдаун полностью
        # Для остальных типов звонков тоже убираем кулдаун
        try:
            ext = Path(sound_path).suffix.lower()
            
            if platform.system() == "Windows":
                try:
                    from PySide6.QtMultimedia import QSound
                    QSound.play(str(sound_path))
                except:
                    self.current_process = subprocess.Popen(
                        ["powershell", "-Command", f'(New-Object Media.SoundPlayer "{sound_path}").PlaySync()'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            else:
                if ext == ".wav":
                    self.current_process = subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac"):
                    self.current_process = subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(sound_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    self.current_process = subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
            
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False
    
    def play_music(self, track_path):
        """Воспроизведение музыки через тот же процесс"""
        if not track_path or not Path(track_path).exists():
            return False
        
        try:
            ext = Path(track_path).suffix.lower()
            
            if platform.system() == "Windows":
                os.startfile(str(track_path))
            else:
                if ext == ".wav":
                    self.current_process = subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac", ".m4a"):
                    self.current_process = subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(track_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    self.current_process = subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
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
