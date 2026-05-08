#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import subprocess
import time
import os
from pathlib import Path


class SoundPlayer:
    def __init__(self):
        self.last_played = {"start": 0.0, "end": 0.0}
        self.min_interval = 60
    
    def play(self, sound_path, sound_type="auto"):
        if not sound_path or not Path(sound_path).exists():
            return False
        
        now = time.time()
        last = self.last_played.get(sound_type, 0.0)
        
        if sound_type != "test" and (now - last) < self.min_interval:
            return False
        
        try:
            ext = Path(sound_path).suffix.lower()
            
            if platform.system() == "Windows":
                try:
                    from PySide6.QtMultimedia import QSound
                    QSound.play(str(sound_path))
                except:
                    subprocess.Popen(
                        ["powershell", "-Command", f'(New-Object Media.SoundPlayer "{sound_path}").PlaySync()'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            else:
                if ext == ".wav":
                    subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac"):
                    subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(sound_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(["aplay", str(sound_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.last_played[sound_type] = now
            return True
            
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False
    
    def play_music(self, track_path):
        if not track_path or not Path(track_path).exists():
            return False
        
        try:
            ext = Path(track_path).suffix.lower()
            
            if platform.system() == "Windows":
                os.startfile(str(track_path))
            else:
                if ext == ".wav":
                    subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in (".mp3", ".ogg", ".flac", ".m4a"):
                    subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(track_path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(["aplay", str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
            print(f"Error playing music: {e}")
            return False
