#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
from pathlib import Path
from src.config import MUSIC_DIR


class MusicPlayer:
    def __init__(self, sound_player=None):
        self.music_folder = None
        self.played_today = set()
        self.last_play_time = 0
        self.delay_minutes = 2
        self.sound_player = sound_player
        
    def set_music_folder(self, folder):
        if folder and Path(folder).exists():
            self.music_folder = Path(folder)
            self.played_today.clear()
            return True
        return False
    
    def get_audio_files(self):
        if not self.music_folder or not self.music_folder.exists():
            return []
        
        extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma"}
        files = []
        for f in self.music_folder.iterdir():
            if f.is_file() and f.suffix.lower() in extensions:
                files.append(f)
        return files
    
    def get_next_track(self):
        files = self.get_audio_files()
        if not files:
            return None
        
        available = [f for f in files if str(f) not in self.played_today]
        if not available:
            self.played_today.clear()
            available = files
        
        track = random.choice(available)
        self.played_today.add(str(track))
        return track
    
    def can_play(self):
        now = time.time()
        return now - self.last_play_time > self.delay_minutes * 60
    
    def mark_played(self):
        self.last_play_time = time.time()
    
    def reset_daily(self):
        self.played_today.clear()
    
    def play_random(self, folder=None):
        if folder:
            self.set_music_folder(folder)
        
        track = self.get_next_track()
        if track and self.sound_player:
            self.sound_player.play_music(str(track))
            self.mark_played()
            return True
        return False
    
    def stop(self):
        """Остановка музыки через общий SoundPlayer"""
        if self.sound_player:
            self.sound_player.stop_all()
